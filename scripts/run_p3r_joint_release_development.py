"""Run frozen P3R-v2 joint-release development on validation only."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import time
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.conditioned_release import (
    conditioned_counts,
    conditioned_log_enrichment,
    public_capacity_layout,
)
from fed_dp_lp.gap_adaptation import (
    client_owned_edges,
    normalize_rows,
    public_svd_encoder,
    release_private_aggregations,
    undirected_adjacency,
)
from fed_dp_lp.joint_release import (
    JOINT_L2_SENSITIVITY,
    joint_scales,
    release_joint_first_hop,
    score_joint_release_pairs,
)
from fed_dp_lp.metrics import paired_summary, roc_auc
from fed_dp_lp.p2_pilot import candidate_arrays, metric_masks, sparse_cosine_scores
from fed_dp_lp.p3_data import load_p3_graph
from fed_dp_lp.systems import peak_resident_memory_bytes


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
CONFIG_PATH = ROOT / "configs/p3r_joint_release_development.json"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p3_split_audit.json"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p3_split_manifest.json"
GAP_RECORDS = ROOT / "results/p3_gap_validation/selected_curve_records.jsonl"
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed/p3_benchmark"
OUTPUT = ROOT / "results/p3r_joint_release_development"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def local_count_vectors(train_positive, train_scores, homes, cells, layout, clients):
    owners = homes[train_positive[:, 0]]
    return tuple(
        conditioned_counts(
            train_positive[owners == client],
            cells,
            train_scores[owners == client],
            layout,
        )
        for client in range(clients)
    )


def full_metrics(labels, scores, masks):
    return {
        scope: {"roc_auc": roc_auc(labels[mask], scores[mask])}
        for scope, mask in masks.items()
    }


def config_key(record):
    return record["histogram_energy_fraction"], record["residual_weight"]


def select_key(records, held_seed):
    candidates = []
    for key in sorted(set(config_key(record) for record in records)):
        values = [
            record["global_roc_auc"]
            for record in records
            if record["seed"] != held_seed and config_key(record) == key
        ]
        if len(values) != 4:
            raise ValueError("nested selection requires four non-held-out seeds")
        gamma, weight = key
        candidates.append((-float(np.mean(values)), gamma, weight, key))
    return min(candidates)[-1]


def release_candidate(
    *, state, encoded, gamma, weight, calibration, config, dataset_index, seed_index,
    clients, hops,
):
    gamma_index = config["candidate"]["histogram_energy_fractions"].index(gamma)
    first_rng = np.random.default_rng(np.random.SeedSequence([
        config["candidate"]["gaussian_stream"], dataset_index, seed_index,
        gamma_index, 1,
    ]))
    started = time.perf_counter()
    first, histogram = release_joint_first_hop(
        state["adjacency"],
        encoded,
        state["local_counts"],
        histogram_energy_fraction=gamma,
        noise_std=calibration.noise_std,
        visibility="visible_messages",
        rng=first_rng,
    )
    channels = [normalize_rows(encoded), normalize_rows(first)]
    if hops == 2:
        second_rng = np.random.default_rng(np.random.SeedSequence([
            config["candidate"]["gaussian_stream"], dataset_index, seed_index,
            gamma_index, 2,
        ]))
        second = release_private_aggregations(
            state["local_edges"],
            first,
            hops=1,
            noise_std=calibration.noise_std,
            visibility="visible_messages",
            rng=second_rng,
            adjacency=state["adjacency"],
        )
        channels.append(second[-1])
    residual = conditioned_log_enrichment(
        histogram,
        state["layout"],
        alpha=config["candidate"]["dirichlet_alpha"],
        clip=config["candidate"]["log_enrichment_clip"],
    )
    scores = score_joint_release_pairs(
        tuple(channels),
        state["public_scores"],
        state["pairs"],
        state["cells"],
        residual,
        state["layout"],
        residual_weight=weight,
    )
    return scores, time.perf_counter() - started


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def main():
    if OUTPUT.exists():
        raise SystemExit("P3R-v2 output exists; refusing overwrite")
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("P3 split audit is not clean")
    epsilon = float(config["privacy"]["epsilon"])
    gap_rows = [json.loads(line) for line in GAP_RECORDS.read_text().splitlines()]
    gap = {
        (row["dataset"], row["seed"]): row
        for row in gap_rows if row["epsilon_target"] == epsilon
    }
    commit = git_head()
    grid_records = []
    held_out_records = []

    for dataset_index, dataset in enumerate(master["datasets"]):
        graph = load_p3_graph(RAW, dataset)
        with np.load(PROCESSED / dataset / "public_layout.npz") as source:
            homes, cells = source["homes"], source["cells"]
        backbone = config["candidate"]["frozen_gap_backbones"][dataset]
        requested_dimension = backbone["projection_dimension"]
        hops = backbone["hops"]
        encoded = public_svd_encoder(
            graph.public_features,
            dimension=requested_dimension,
            random_state=config["candidate"]["semantic_encoder_seed_base"]
            + requested_dimension,
        )
        layout = public_capacity_layout(
            graph.public_features,
            cells,
            np.asarray(config["candidate"]["bin_edges"]),
            maximum_pairs=config["candidate"]["capacity_sample_maximum"],
            seed=config["candidate"]["capacity_seed"],
            dirichlet_alpha=config["candidate"]["dirichlet_alpha"],
        )
        calibration = calibrate_gaussian(
            target_epsilon=epsilon,
            delta=config["privacy"]["delta"],
            sensitivity=JOINT_L2_SENSITIVITY,
            steps=hops,
            orders=DEFAULT_ORDERS,
        )
        per_seed = {}
        for seed_index, seed in enumerate(master["split"]["seeds"]):
            with np.load(
                PROCESSED / dataset / f"seed_{seed}_development.npz",
                allow_pickle=False,
            ) as source:
                train_positive = source["train_positive"]
                positive = source["validation_positive"]
                negative = source["validation_negative"]
            pairs, labels = candidate_arrays(positive, negative)
            local_edges = client_owned_edges(
                train_positive, homes, clients=master["clients"]
            )
            train_scores = sparse_cosine_scores(
                graph.public_features, train_positive
            )
            state = {
                "pairs": pairs,
                "labels": labels,
                "masks": metric_masks(pairs, homes),
                "public_scores": sparse_cosine_scores(graph.public_features, pairs),
                "local_edges": local_edges,
                "adjacency": undirected_adjacency(local_edges, len(homes)),
                "local_counts": local_count_vectors(
                    train_positive, train_scores, homes, cells, layout,
                    master["clients"],
                ),
                "cells": cells,
                "layout": layout,
                "seed_index": seed_index,
                "train_edges": len(train_positive),
            }
            per_seed[seed] = state
            for gamma in config["candidate"]["histogram_energy_fractions"]:
                for weight in config["candidate"]["residual_weights"]:
                    scores, elapsed = release_candidate(
                        state=state, encoded=encoded, gamma=gamma, weight=weight,
                        calibration=calibration, config=config,
                        dataset_index=dataset_index, seed_index=seed_index,
                        clients=master["clients"], hops=hops,
                    )
                    grid_records.append({
                        "dataset": dataset,
                        "seed": seed,
                        "histogram_energy_fraction": gamma,
                        "residual_weight": weight,
                        "global_roc_auc": roc_auc(labels, scores),
                        "release_seconds": elapsed,
                    })

        dataset_grid = [r for r in grid_records if r["dataset"] == dataset]
        for seed in master["split"]["seeds"]:
            gamma, weight = select_key(dataset_grid, seed)
            state = per_seed[seed]
            scores, elapsed = release_candidate(
                state=state, encoded=encoded, gamma=gamma, weight=weight,
                calibration=calibration, config=config,
                dataset_index=dataset_index, seed_index=state["seed_index"],
                clients=master["clients"], hops=hops,
            )
            aggregation_scale, histogram_scale = joint_scales(gamma)
            release_dimension = hops * len(homes) * encoded.shape[1] + layout.dimension
            baseline = gap[(dataset, seed)]
            held_out_records.append({
                "protocol": "P3R_JOINT_RELEASE_DEVELOPMENT_v2",
                "role": "leave_one_seed_out_held_out_development",
                "code_commit": commit,
                "dataset": dataset,
                "seed": seed,
                "epsilon_target": epsilon,
                "split": "validation",
                "test_accessed": False,
                "master_config_sha256": sha256(MASTER_PATH),
                "p3r_config_sha256": sha256(CONFIG_PATH),
                "split_manifest_sha256": sha256(SPLIT_MANIFEST_PATH),
                "privacy": asdict(calibration),
                "adjacency": "add_remove_one_canonical_undirected_edge",
                "l2_sensitivity_per_release": JOINT_L2_SENSITIVITY,
                "release_count": hops,
                "visibility": "individually_visible_client_messages",
                "server_sum_simulation": "distribution_equivalent_sqrt_K_gaussian",
                "selected_config": {
                    "projection_dimension_requested": requested_dimension,
                    "projection_dimension": encoded.shape[1],
                    "hops": hops,
                    "histogram_energy_fraction": gamma,
                    "residual_weight": weight,
                    "aggregation_scale": aggregation_scale,
                    "histogram_scale": histogram_scale,
                    "scale_identity": 2 * aggregation_scale**2 + histogram_scale**2,
                },
                "train_edge_count": state["train_edges"],
                "client_train_edge_counts": [len(x) for x in state["local_edges"]],
                "histogram_dimension": layout.dimension,
                "release_dimension": release_dimension,
                "client_message_bytes": master["clients"] * release_dimension * 8,
                "server_release_bytes": release_dimension * 8,
                "wall_time_seconds": elapsed,
                "peak_resident_memory_bytes": peak_resident_memory_bytes(),
                "metrics": {
                    "joint_release": full_metrics(
                        state["labels"], scores, state["masks"]
                    ),
                    "gap_style": baseline["metrics"]["gap_style_lp"],
                },
            })

    comparisons = {}
    for dataset in master["datasets"]:
        rows = [r for r in held_out_records if r["dataset"] == dataset]
        comparisons[dataset] = {}
        for scope in ("global", "cross"):
            candidate = np.asarray([
                r["metrics"]["joint_release"][scope]["roc_auc"] for r in rows
            ])
            baseline = np.asarray([
                r["metrics"]["gap_style"][scope]["roc_auc"] for r in rows
            ])
            comparisons[dataset][scope] = paired_summary(candidate, baseline)
    global_gains = [comparisons[d]["global"]["mean_difference"] for d in master["datasets"]]
    cross_gains = [comparisons[d]["cross"]["mean_difference"] for d in master["datasets"]]
    gates = config["go_no_go"]
    checks = {
        "positive_global_ci_count": sum(
            comparisons[d]["global"]["ci95_low"] > 0 for d in master["datasets"]
        ) >= gates["minimum_datasets_with_positive_global_95pct_ci"],
        "positive_cross_ci_count": sum(
            comparisons[d]["cross"]["ci95_low"] > 0 for d in master["datasets"]
        ) >= gates["minimum_datasets_with_positive_cross_95pct_ci"],
        "macro_global_gain": float(np.mean(global_gains))
        >= gates["minimum_macro_mean_global_gain"],
        "macro_cross_gain": float(np.mean(cross_gains))
        >= gates["minimum_macro_mean_cross_gain"],
        "global_drop_boundary": min(global_gains)
        >= gates["maximum_allowed_dataset_mean_global_drop"],
        "cross_drop_boundary": min(cross_gains)
        >= gates["maximum_allowed_dataset_mean_cross_drop"],
        "all_metrics_finite": all(
            np.isfinite(value) for record in held_out_records
            for method in record["metrics"].values()
            for scope in method.values() for value in scope.values()
        ),
        "test_never_accessed": all(not r["test_accessed"] for r in held_out_records),
    }
    decision = (
        "GO_TO_FRESH_CONFIRMATORY_PROTOCOL"
        if all(checks.values()) else "NO_GO_REJECT_JOINT_RELEASE_CANDIDATE"
    )
    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "grid_records.jsonl", grid_records)
    write_jsonl(OUTPUT / "held_out_records.jsonl", held_out_records)
    (OUTPUT / "summary.json").write_text(json.dumps({
        "protocol": "P3R_JOINT_RELEASE_DEVELOPMENT_v2",
        "role": config["role"],
        "grid_record_count": len(grid_records),
        "held_out_record_count": len(held_out_records),
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
