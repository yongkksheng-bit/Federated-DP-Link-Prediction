"""Run the frozen P5F privacy-utility frontier validation."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
from dataclasses import asdict

import numpy as np
from scipy.stats import spearmanr

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.frontier import (
    degree_upper_energy_ratio,
    expected_noise_energy,
    gaussian_norm_interval,
    signal_noise_energy_ratio,
)
from fed_dp_lp.gap_adaptation import (
    UNDIRECTED_EDGE_L2_SENSITIVITY,
    cached_public_svd_encoder,
    client_owned_edges,
    normalize_rows,
    release_private_aggregations,
    score_pairs_from_channels,
    undirected_adjacency,
)
from fed_dp_lp.metrics import roc_auc
from fed_dp_lp.p2_pilot import candidate_arrays, metric_masks, sparse_cosine_scores
from fed_dp_lp.p3_data import load_p3_graph


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
CONFIG_PATH = ROOT / "configs/p5f_frontier_validation.json"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p3_split_audit.json"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p3_split_manifest.json"
PRIOR_GAP_PATH = ROOT / "results/p3_gap_validation/selected_curve_records.jsonl"
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed/p3_benchmark"
CACHE = ROOT / "data/cache/public_svd"
OUTPUT = ROOT / "results/p5f_frontier_validation"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def scoped_auc(labels, scores, masks):
    return {scope: roc_auc(labels[mask], scores[mask]) for scope, mask in masks.items()}


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def main():
    if OUTPUT.exists():
        raise SystemExit("P5F output exists; refusing overwrite")
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("P3 split audit is not clean")
    prior_rows = [json.loads(line) for line in PRIOR_GAP_PATH.read_text().splitlines()]
    prior = {(r["dataset"], r["seed"], float(r["epsilon_target"])): r for r in prior_rows}
    commit = git_head()
    records = []
    for dataset_index, dataset in enumerate(master["datasets"]):
        print(f"[{dataset}] frontier start", flush=True)
        graph = load_p3_graph(RAW, dataset)
        with np.load(PROCESSED / dataset / "public_layout.npz") as source:
            homes = source["homes"]
        backbone = config["frozen_gap_backbones"][dataset]
        dimension, hops = backbone["projection_dimension"], backbone["hops"]
        cache_path = CACHE / f"{dataset}_d{dimension}_s{20260724 + dimension}.npz"
        encoded = cached_public_svd_encoder(
            graph.public_features,
            dimension=dimension,
            random_state=20260724 + dimension,
            cache_path=cache_path,
        )
        for seed in master["split"]["seeds"]:
            with np.load(
                PROCESSED / dataset / f"seed_{seed}_development.npz",
                allow_pickle=False,
            ) as source:
                train_positive = source["train_positive"]
                positive = source["validation_positive"]
                negative = source["validation_negative"]
            pairs, labels = candidate_arrays(positive, negative)
            masks = metric_masks(pairs, homes)
            public_scores = sparse_cosine_scores(graph.public_features, pairs)
            public_auc = scoped_auc(labels, public_scores, masks)
            local_edges = client_owned_edges(
                train_positive, homes, clients=master["clients"]
            )
            adjacency = undirected_adjacency(local_edges, len(homes))
            first_signal = adjacency @ normalize_rows(encoded)
            degrees = np.asarray(adjacency.sum(axis=1)).ravel()
            for epsilon_index, epsilon in enumerate(config["epsilon_grid"]):
                calibration = calibrate_gaussian(
                    target_epsilon=epsilon,
                    delta=config["privacy"]["delta"],
                    sensitivity=UNDIRECTED_EDGE_L2_SENSITIVITY,
                    steps=hops,
                    orders=DEFAULT_ORDERS,
                )
                for visibility in config["visibility_models"]:
                    stream = config["rng_streams"][visibility]
                    rng = np.random.default_rng(np.random.SeedSequence([
                        stream, dataset_index, seed, epsilon_index, dimension, hops,
                    ]))
                    channels = release_private_aggregations(
                        local_edges,
                        encoded,
                        hops=hops,
                        noise_std=calibration.noise_std,
                        visibility=visibility,
                        rng=rng,
                        adjacency=adjacency,
                    )
                    private_scores = score_pairs_from_channels(channels, pairs)
                    private_auc = scoped_auc(labels, private_scores, masks)
                    actual_ratio = signal_noise_energy_ratio(
                        first_signal,
                        noise_std=calibration.noise_std,
                        clients=master["clients"],
                        visibility=visibility,
                    )
                    upper_ratio = degree_upper_energy_ratio(
                        degrees,
                        encoding_dimension=encoded.shape[1],
                        noise_std=calibration.noise_std,
                        clients=master["clients"],
                        visibility=visibility,
                    )
                    release_dimension = len(homes) * encoded.shape[1]
                    lower, upper = gaussian_norm_interval(
                        release_dimension=release_dimension,
                        noise_std=calibration.noise_std,
                        clients=master["clients"],
                        visibility=visibility,
                        failure_probability=config["failure_probability"],
                    )
                    prior_error = None
                    if visibility == "visible_messages":
                        old = prior[(dataset, seed, float(epsilon))]
                        prior_error = max(
                            abs(private_auc[scope] - old["metrics"]["gap_style_lp"][scope]["roc_auc"])
                            for scope in ("global", "intra", "cross")
                        )
                    records.append({
                        "protocol": config["protocol"],
                        "role": config["role"],
                        "code_commit": commit,
                        "dataset": dataset,
                        "seed": seed,
                        "epsilon_target": epsilon,
                        "visibility": visibility,
                        "split": "validation",
                        "test_accessed": False,
                        "config_sha256": sha256(CONFIG_PATH),
                        "master_config_sha256": sha256(MASTER_PATH),
                        "split_manifest_sha256": sha256(SPLIT_MANIFEST_PATH),
                        "public_encoding_cache": str(cache_path.relative_to(ROOT)),
                        "public_encoding_cache_sha256": sha256(cache_path),
                        "privacy": asdict(calibration),
                        "l2_sensitivity_per_release": UNDIRECTED_EDGE_L2_SENSITIVITY,
                        "release_count": hops,
                        "client_count": master["clients"],
                        "projection_dimension": encoded.shape[1],
                        "first_hop_release_dimension": release_dimension,
                        "first_hop_signal_frobenius_squared": float(np.linalg.norm(first_signal) ** 2),
                        "degree_squared_sum": float(np.sum(degrees**2)),
                        "expected_first_hop_noise_energy": expected_noise_energy(
                            release_dimension=release_dimension,
                            noise_std=calibration.noise_std,
                            clients=master["clients"],
                            visibility=visibility,
                        ),
                        "frontier_signal_ratio": actual_ratio,
                        "frontier_degree_upper_ratio": upper_ratio,
                        "noise_norm_interval_95": [lower, upper],
                        "visible_prior_max_auc_error": prior_error,
                        "metrics": {
                            "gap_style": private_auc,
                            "public_cosine": public_auc,
                            "gain_over_public": {
                                scope: private_auc[scope] - public_auc[scope]
                                for scope in ("global", "intra", "cross")
                            },
                        },
                    })
        print(f"[{dataset}] frontier complete", flush=True)

    cells = []
    for dataset in master["datasets"]:
        for epsilon in config["epsilon_grid"]:
            for visibility in config["visibility_models"]:
                subset = [r for r in records if r["dataset"] == dataset
                          and r["epsilon_target"] == epsilon
                          and r["visibility"] == visibility]
                cells.append({
                    "dataset": dataset,
                    "epsilon": epsilon,
                    "visibility": visibility,
                    "mean_log10_frontier_signal_ratio": float(np.mean([
                        np.log10(max(r["frontier_signal_ratio"], 1e-300)) for r in subset
                    ])),
                    "mean_global_auc_gain": float(np.mean([
                        r["metrics"]["gain_over_public"]["global"] for r in subset
                    ])),
                    "mean_cross_auc_gain": float(np.mean([
                        r["metrics"]["gain_over_public"]["cross"] for r in subset
                    ])),
                })
    def correlation(subset):
        result = spearmanr(
            [x["mean_log10_frontier_signal_ratio"] for x in subset],
            [x["mean_global_auc_gain"] for x in subset],
        )
        return {"n": len(subset), "spearman": float(result.statistic), "pvalue": float(result.pvalue)}
    correlations = {
        "all": correlation(cells),
        "visible_messages": correlation([x for x in cells if x["visibility"] == "visible_messages"]),
        "ideal_secagg": correlation([x for x in cells if x["visibility"] == "ideal_secagg"]),
    }
    visible_errors = [r["visible_prior_max_auc_error"] for r in records
                      if r["visibility"] == "visible_messages"]
    ratios = []
    for dataset in master["datasets"]:
        for seed in master["split"]["seeds"]:
            for epsilon in config["epsilon_grid"]:
                pair = [r for r in records if r["dataset"] == dataset and r["seed"] == seed
                        and r["epsilon_target"] == epsilon]
                energy = {r["visibility"]: r["expected_first_hop_noise_energy"] for r in pair}
                ratios.append(energy["visible_messages"] / energy["ideal_secagg"])
    gate = config["analysis_gate"]
    checks = {
        "all_cell_spearman": correlations["all"]["spearman"] >= gate["minimum_all_cell_spearman"],
        "visible_cell_spearman": correlations["visible_messages"]["spearman"]
        >= gate["minimum_visible_cell_spearman"],
        "visible_reproduction": max(visible_errors)
        <= gate["maximum_visible_reproduction_auc_error"],
        "noise_energy_ratio": all(np.isclose(x, gate["required_noise_energy_ratio_visible_over_ideal"]) for x in ratios),
        "all_metrics_finite": all(np.isfinite(value) for r in records
            for method in r["metrics"].values() for value in (
                method.values() if isinstance(method, dict) else []
            )),
        "test_never_accessed": all(not r["test_accessed"] for r in records),
    }
    decision = "FRONTIER_INDEX_SUPPORTED_FOR_FRESH_VALIDATION" if all(checks.values()) else "FRONTIER_INDEX_REQUIRES_REVISION"
    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "records.jsonl", records)
    write_jsonl(OUTPUT / "cells.jsonl", cells)
    (OUTPUT / "summary.json").write_text(json.dumps({
        "protocol": config["protocol"],
        "record_count": len(records),
        "cell_count": len(cells),
        "correlations": correlations,
        "max_visible_reproduction_auc_error": max(visible_errors),
        "noise_energy_ratio_min": min(ratios),
        "noise_energy_ratio_max": max(ratios),
        "checks": checks,
        "decision": decision,
        "test_accessed": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
