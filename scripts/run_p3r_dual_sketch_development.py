"""Run frozen P3R dual-sketch development without accessing encrypted test."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import time
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.dual_sketch import (
    joint_public_query,
    public_rademacher_signatures,
    score_dual_sketch_pairs,
)
from fed_dp_lp.gap_adaptation import (
    UNDIRECTED_EDGE_L2_SENSITIVITY,
    client_owned_edges,
    public_svd_encoder,
    release_private_aggregations,
    undirected_adjacency,
)
from fed_dp_lp.metrics import paired_summary, roc_auc
from fed_dp_lp.p2_pilot import candidate_arrays, metric_masks, sparse_cosine_scores
from fed_dp_lp.p3_data import load_p3_graph
from fed_dp_lp.systems import peak_resident_memory_bytes


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
CONFIG_PATH = ROOT / "configs/p3r_dual_sketch_development.json"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p3_split_audit.json"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p3_split_manifest.json"
GAP_RECORDS = ROOT / "results/p3_gap_validation/selected_curve_records.jsonl"
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed/p3_benchmark"
OUTPUT = ROOT / "results/p3r_dual_sketch_development"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def config_key(record):
    return (
        record["semantic_dimension"],
        record["topology_dimension"],
        record["semantic_fraction"],
        record["decoder_mode"],
        record["public_weight"],
        record["topology_weight"],
    )


def select_key(records, held_seed):
    keys = sorted(set(config_key(record) for record in records))
    candidates = []
    for key in keys:
        values = [
            record["global_roc_auc"]
            for record in records
            if record["seed"] != held_seed and config_key(record) == key
        ]
        if len(values) != 4:
            raise ValueError("nested selection requires four non-held-out seeds")
        semantic_dim, topology_dim, fraction, mode, public_weight, topology_weight = key
        candidates.append((
            -float(np.mean(values)),
            semantic_dim + topology_dim,
            -fraction,
            topology_weight,
            public_weight,
            mode,
            key,
        ))
    return min(candidates)[-1]


def full_metrics(labels, scores, masks):
    return {
        scope: {"roc_auc": roc_auc(labels[mask], scores[mask])}
        for scope, mask in masks.items()
    }


def main():
    if OUTPUT.exists():
        raise SystemExit("P3R output exists; refusing overwrite")
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("P3 split audit is not clean")
    epsilon = config["privacy"]["epsilon"]
    calibration = calibrate_gaussian(
        target_epsilon=epsilon,
        delta=config["privacy"]["delta"],
        sensitivity=UNDIRECTED_EDGE_L2_SENSITIVITY,
        steps=config["privacy"]["releases"],
        orders=DEFAULT_ORDERS,
    )
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
            homes = source["homes"]
        semantic_dimensions = sorted({pair[0] for pair in config["candidate"]["dimension_pairs"]})
        semantic = {
            dimension: public_svd_encoder(
                graph.public_features,
                dimension=dimension,
                random_state=config["candidate"]["semantic_encoder_seed"] + dimension,
            )
            for dimension in semantic_dimensions
        }
        maximum_topology = max(pair[1] for pair in config["candidate"]["dimension_pairs"])
        topology_max = public_rademacher_signatures(
            graph.public_features.shape[0],
            dimension=maximum_topology,
            seed=config["candidate"]["topology_signature_seed"] + dataset_index,
        )
        topology = {
            dimension: topology_max[:, :dimension] * np.sqrt(maximum_topology / dimension)
            for dimension in sorted({pair[1] for pair in config["candidate"]["dimension_pairs"]})
        }
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
            masks = metric_masks(pairs, homes)
            public_scores = sparse_cosine_scores(graph.public_features, pairs)
            local_edges = client_owned_edges(
                train_positive, homes, clients=master["clients"]
            )
            adjacency = undirected_adjacency(local_edges, graph.public_features.shape[0])
            for semantic_dimension, topology_dimension in config["candidate"]["dimension_pairs"]:
                for fraction_index, fraction in enumerate(
                    config["candidate"]["semantic_energy_fractions"]
                ):
                    query = joint_public_query(
                        semantic[semantic_dimension],
                        topology[topology_dimension],
                        semantic_fraction=fraction,
                    )
                    rng = np.random.default_rng(np.random.SeedSequence([
                        config["candidate"]["gaussian_stream"],
                        dataset_index,
                        seed_index,
                        semantic_dimension,
                        topology_dimension,
                        fraction_index,
                    ]))
                    started = time.perf_counter()
                    released = release_private_aggregations(
                        local_edges,
                        query,
                        hops=1,
                        noise_std=calibration.noise_std,
                        visibility="visible_messages",
                        rng=rng,
                        adjacency=adjacency,
                    )[1]
                    release_seconds = time.perf_counter() - started
                    effective_noise = calibration.noise_std * np.sqrt(master["clients"])
                    for mode in config["candidate"]["decoder_modes"]:
                        for public_weight in config["candidate"]["public_weights"]:
                            for topology_weight in config["candidate"]["topology_weights"]:
                                key = (
                                    semantic_dimension, topology_dimension, fraction,
                                    mode, public_weight, topology_weight,
                                )
                                scores = score_dual_sketch_pairs(
                                    public_scores,
                                    released,
                                    pairs,
                                    semantic_dimension=semantic_dimension,
                                    mode=mode,
                                    effective_noise_std=effective_noise,
                                    public_weight=public_weight,
                                    semantic_weight=config["candidate"]["semantic_weight"],
                                    topology_weight=topology_weight,
                                )
                                record = {
                                    "dataset": dataset,
                                    "seed": seed,
                                    "semantic_dimension": semantic_dimension,
                                    "topology_dimension": topology_dimension,
                                    "joint_dimension": semantic_dimension + topology_dimension,
                                    "semantic_fraction": fraction,
                                    "decoder_mode": mode,
                                    "public_weight": public_weight,
                                    "topology_weight": topology_weight,
                                    "global_roc_auc": roc_auc(labels, scores),
                                    "release_seconds": release_seconds,
                                }
                                grid_records.append(record)
            per_seed[seed] = {
                "labels": labels,
                "masks": masks,
                "pairs": pairs,
                "public_scores": public_scores,
                "local_edges": local_edges,
                "adjacency": adjacency,
                "seed_index": seed_index,
                "train_edges": len(train_positive),
            }

        dataset_grid = [record for record in grid_records if record["dataset"] == dataset]
        for seed in master["split"]["seeds"]:
            selected = select_key(dataset_grid, seed)
            semantic_dimension, topology_dimension, fraction, mode, public_weight, topology_weight = selected
            fraction_index = config["candidate"]["semantic_energy_fractions"].index(fraction)
            query = joint_public_query(
                semantic[semantic_dimension],
                topology[topology_dimension],
                semantic_fraction=fraction,
            )
            rng = np.random.default_rng(np.random.SeedSequence([
                config["candidate"]["gaussian_stream"],
                dataset_index,
                per_seed[seed]["seed_index"],
                semantic_dimension,
                topology_dimension,
                fraction_index,
            ]))
            released = release_private_aggregations(
                per_seed[seed]["local_edges"],
                query,
                hops=1,
                noise_std=calibration.noise_std,
                visibility="visible_messages",
                rng=rng,
                adjacency=per_seed[seed]["adjacency"],
            )[1]
            candidate_scores = score_dual_sketch_pairs(
                per_seed[seed]["public_scores"],
                released,
                per_seed[seed]["pairs"],
                semantic_dimension=semantic_dimension,
                mode=mode,
                effective_noise_std=calibration.noise_std * np.sqrt(master["clients"]),
                public_weight=public_weight,
                semantic_weight=config["candidate"]["semantic_weight"],
                topology_weight=topology_weight,
            )
            baseline = gap[(dataset, seed)]
            held_out_records.append({
                "protocol": "P3R_DUAL_SKETCH_DEVELOPMENT_v1",
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
                "l2_sensitivity": UNDIRECTED_EDGE_L2_SENSITIVITY,
                "visibility": "individually_visible_client_messages",
                "selected_config": {
                    "semantic_dimension": semantic_dimension,
                    "topology_dimension": topology_dimension,
                    "joint_dimension": semantic_dimension + topology_dimension,
                    "semantic_fraction": fraction,
                    "decoder_mode": mode,
                    "public_weight": public_weight,
                    "semantic_weight": config["candidate"]["semantic_weight"],
                    "topology_weight": topology_weight,
                },
                "train_edge_count": per_seed[seed]["train_edges"],
                "release_dimension": graph.public_features.shape[0]
                * (semantic_dimension + topology_dimension),
                "client_message_bytes": master["clients"]
                * graph.public_features.shape[0]
                * (semantic_dimension + topology_dimension)
                * np.dtype(np.float64).itemsize,
                "peak_resident_memory_bytes": peak_resident_memory_bytes(),
                "metrics": {
                    "dual_sketch": full_metrics(
                        per_seed[seed]["labels"], candidate_scores, per_seed[seed]["masks"]
                    ),
                    "gap_style": baseline["metrics"]["gap_style_lp"],
                },
            })

    comparisons = {}
    for dataset in master["datasets"]:
        rows = [record for record in held_out_records if record["dataset"] == dataset]
        comparisons[dataset] = {}
        for scope in ("global", "cross"):
            candidate = np.asarray([
                record["metrics"]["dual_sketch"][scope]["roc_auc"] for record in rows
            ])
            baseline = np.asarray([
                record["metrics"]["gap_style"][scope]["roc_auc"] for record in rows
            ])
            comparisons[dataset][scope] = paired_summary(candidate, baseline)
    gates = config["go_no_go"]
    global_gains = [comparisons[d]["global"]["mean_difference"] for d in master["datasets"]]
    cross_gains = [comparisons[d]["cross"]["mean_difference"] for d in master["datasets"]]
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
            np.isfinite(value)
            for record in held_out_records
            for method in record["metrics"].values()
            for scope in method.values()
            for value in scope.values()
        ),
        "test_never_accessed": all(not record["test_accessed"] for record in held_out_records),
    }
    decision = (
        "GO_TO_FRESH_CONFIRMATORY_PROTOCOL"
        if all(checks.values())
        else "NO_GO_REJECT_DUAL_SKETCH_CANDIDATE"
    )
    OUTPUT.mkdir(parents=True)
    with (OUTPUT / "grid_records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in grid_records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    with (OUTPUT / "held_out_records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in held_out_records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(json.dumps({
        "protocol": "P3R_DUAL_SKETCH_DEVELOPMENT_v1",
        "role": config["role"],
        "grid_record_count": len(grid_records),
        "held_out_record_count": len(held_out_records),
        "privacy": asdict(calibration),
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
