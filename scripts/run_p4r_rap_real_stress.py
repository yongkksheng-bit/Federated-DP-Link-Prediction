"""Run fixed RAP on P3 validation without accessing encrypted test data."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.gap_adaptation import (
    cached_public_svd_encoder,
    client_owned_edges,
    normalize_rows,
    release_private_aggregations,
    undirected_adjacency,
)
from fed_dp_lp.metrics import paired_summary, roc_auc
from fed_dp_lp.p2_pilot import candidate_arrays, metric_masks
from fed_dp_lp.p3_data import load_p3_graph
from fed_dp_lp.reciprocal_profile import (
    RAP_L2_SENSITIVITY,
    joint_profile_scales,
    reciprocal_profile_counts,
    release_joint_semantic_profile,
    score_rap_pairs,
)
from fed_dp_lp.systems import peak_resident_memory_bytes


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
CONFIG_PATH = ROOT / "configs/p4r_rap_real_stress.json"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p3_split_audit.json"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p3_split_manifest.json"
GAP_RECORDS = ROOT / "results/p3_gap_validation/selected_curve_records.jsonl"
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed/p3_benchmark"
OUTPUT = ROOT / "results/p4r_rap_real_stress"
CACHE = ROOT / "data/cache/public_svd"
STREAM = 20260821


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def local_profiles(local_edges, cells, nodes):
    return tuple(
        reciprocal_profile_counts(edges, cells, node_count=nodes)
        for edges in local_edges
    )


def full_metrics(labels, scores, masks):
    return {scope: {"roc_auc": roc_auc(labels[mask], scores[mask])}
            for scope, mask in masks.items()}


def main():
    if OUTPUT.exists():
        raise SystemExit("P4R real-stress output exists; refusing overwrite")
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("P3 split audit is not clean")
    epsilon = float(config["privacy"]["epsilon"])
    gap_rows = [json.loads(line) for line in GAP_RECORDS.read_text().splitlines()]
    gap = {(r["dataset"], r["seed"]): r for r in gap_rows
           if r["epsilon_target"] == epsilon}
    commit = git_head()
    records = []
    candidate = config["candidate"]
    for dataset_index, dataset in enumerate(master["datasets"]):
        print(f"[{dataset}] loading public graph", flush=True)
        graph = load_p3_graph(RAW, dataset)
        with np.load(PROCESSED / dataset / "public_layout.npz") as source:
            homes, cells = source["homes"], source["cells"]
        backbone = candidate["frozen_gap_backbones"][dataset]
        requested_dimension, hops = (
            backbone["projection_dimension"], backbone["hops"]
        )
        print(
            f"[{dataset}] encoding n={len(homes)} features={graph.public_features.shape[1]} "
            f"cells={int(np.max(cells)) + 1} dim={requested_dimension} hops={hops}",
            flush=True,
        )
        cache_path = CACHE / (
            f"{dataset}_d{requested_dimension}_s{20260724 + requested_dimension}.npz"
        )
        encoded = cached_public_svd_encoder(
            graph.public_features,
            dimension=requested_dimension,
            random_state=20260724 + requested_dimension,
            cache_path=cache_path,
        )
        print(f"[{dataset}] public encoding complete", flush=True)
        calibration = calibrate_gaussian(
            target_epsilon=epsilon,
            delta=config["privacy"]["delta"],
            sensitivity=RAP_L2_SENSITIVITY,
            steps=hops,
            orders=DEFAULT_ORDERS,
        )
        for seed_index, seed in enumerate(master["split"]["seeds"]):
            print(f"[{dataset}] seed={seed} start", flush=True)
            with np.load(
                PROCESSED / dataset / f"seed_{seed}_development.npz",
                allow_pickle=False,
            ) as source:
                train_positive = source["train_positive"]
                positive = source["validation_positive"]
                negative = source["validation_negative"]
            pairs, labels = candidate_arrays(positive, negative)
            masks = metric_masks(pairs, homes)
            local_edges = client_owned_edges(
                train_positive, homes, clients=master["clients"]
            )
            adjacency = undirected_adjacency(local_edges, len(homes))
            profiles = local_profiles(local_edges, cells, len(homes))
            rng = np.random.default_rng(np.random.SeedSequence([
                STREAM, dataset_index, seed_index,
            ]))
            semantic, noisy_profiles = release_joint_semantic_profile(
                adjacency,
                encoded,
                profiles,
                profile_energy_fraction=candidate["profile_energy_fraction"],
                noise_std=calibration.noise_std,
                visibility="visible_messages",
                rng=rng,
            )
            channels = [normalize_rows(encoded), normalize_rows(semantic)]
            if hops == 2:
                second_rng = np.random.default_rng(np.random.SeedSequence([
                    STREAM, dataset_index, seed_index, 2,
                ]))
                second = release_private_aggregations(
                    local_edges,
                    semantic,
                    hops=1,
                    noise_std=calibration.noise_std,
                    visibility="visible_messages",
                    rng=second_rng,
                    adjacency=adjacency,
                )
                channels.append(second[-1])
            _, profile_scale = joint_profile_scales(
                candidate["profile_energy_fraction"]
            )
            effective_profile_noise = (
                calibration.noise_std * np.sqrt(master["clients"]) / profile_scale
            )
            scores = score_rap_pairs(
                tuple(channels),
                noisy_profiles,
                pairs,
                cells,
                profile_weight=candidate["profile_weight"],
                prior_strength=candidate["prior_strength"],
                effective_profile_noise_std=effective_profile_noise,
            )
            baseline = gap[(dataset, seed)]
            release_dimension = (
                hops * len(homes) * encoded.shape[1]
                + len(homes) * (int(np.max(cells)) + 1)
            )
            records.append({
                "protocol": config["protocol"],
                "role": config["role"],
                "code_commit": commit,
                "dataset": dataset,
                "seed": seed,
                "split": "validation",
                "test_accessed": False,
                "config_sha256": sha256(CONFIG_PATH),
                "master_config_sha256": sha256(MASTER_PATH),
                "split_manifest_sha256": sha256(SPLIT_MANIFEST_PATH),
                "public_encoding_cache": str(cache_path.relative_to(ROOT)),
                "public_encoding_cache_sha256": sha256(cache_path),
                "privacy": asdict(calibration),
                "l2_sensitivity_per_release": RAP_L2_SENSITIVITY,
                "release_count": hops,
                "visibility": "individually_visible_client_messages",
                "selected_config": {
                    "profile_energy_fraction": candidate["profile_energy_fraction"],
                    "profile_weight": candidate["profile_weight"],
                    "prior_strength": candidate["prior_strength"],
                    "projection_dimension_requested": requested_dimension,
                    "projection_dimension": encoded.shape[1],
                    "hops": hops,
                },
                "client_train_edge_counts": [len(x) for x in local_edges],
                "profile_dimension": len(homes) * (int(np.max(cells)) + 1),
                "release_dimension": release_dimension,
                "client_message_bytes": master["clients"] * release_dimension * 8,
                "server_release_bytes": release_dimension * 8,
                "peak_resident_memory_bytes": peak_resident_memory_bytes(),
                "metrics": {
                    "rap": full_metrics(labels, scores, masks),
                    "gap_style": baseline["metrics"]["gap_style_lp"],
                },
            })
            print(f"[{dataset}] seed={seed} complete", flush=True)
        print(f"[{dataset}] complete", flush=True)
    comparisons = {}
    for dataset in master["datasets"]:
        rows = [r for r in records if r["dataset"] == dataset]
        comparisons[dataset] = {}
        for scope in ("global", "cross"):
            rap = np.asarray([r["metrics"]["rap"][scope]["roc_auc"] for r in rows])
            baseline = np.asarray([
                r["metrics"]["gap_style"][scope]["roc_auc"] for r in rows
            ])
            comparisons[dataset][scope] = paired_summary(rap, baseline)
    global_gains = [comparisons[d]["global"]["mean_difference"] for d in master["datasets"]]
    cross_gains = [comparisons[d]["cross"]["mean_difference"] for d in master["datasets"]]
    gate = config["go_no_go"]
    checks = {
        "positive_global_ci_count": sum(
            comparisons[d]["global"]["ci95_low"] > 0 for d in master["datasets"]
        ) >= gate["minimum_datasets_with_positive_global_95pct_ci"],
        "positive_cross_ci_count": sum(
            comparisons[d]["cross"]["ci95_low"] > 0 for d in master["datasets"]
        ) >= gate["minimum_datasets_with_positive_cross_95pct_ci"],
        "macro_global_gain": float(np.mean(global_gains))
        >= gate["minimum_macro_mean_global_gain"],
        "macro_cross_gain": float(np.mean(cross_gains))
        >= gate["minimum_macro_mean_cross_gain"],
        "global_drop_boundary": min(global_gains)
        >= gate["maximum_allowed_dataset_mean_global_drop"],
        "cross_drop_boundary": min(cross_gains)
        >= gate["maximum_allowed_dataset_mean_cross_drop"],
        "all_metrics_finite": all(
            np.isfinite(value) for record in records
            for method in record["metrics"].values()
            for scope in method.values() for value in scope.values()
        ),
        "test_never_accessed": all(not r["test_accessed"] for r in records),
    }
    decision = "GO_REGISTER_FRESH_REAL_SOURCES" if all(checks.values()) else "NO_GO_REJECT_RAP_REAL_STRESS"
    OUTPUT.mkdir(parents=True)
    with (OUTPUT / "records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(json.dumps({
        "protocol": config["protocol"],
        "record_count": len(records),
        "comparisons_vs_gap": comparisons,
        "macro_mean_global_gain": float(np.mean(global_gains)),
        "macro_mean_cross_gain": float(np.mean(cross_gains)),
        "checks": checks,
        "decision": decision,
        "test_accessed": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
