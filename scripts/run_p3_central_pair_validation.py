"""Validate the closest formal centralized edge-DP LP baseline on P3 validation."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import time
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.central_pair_dp import (
    EDGE_RECORD_MULTIPLICITY,
    bounded_pair_design,
    stable_negative_pairs,
    train_private_logistic,
)
from fed_dp_lp.gap_adaptation import public_svd_encoder
from fed_dp_lp.metrics import average_precision, roc_auc
from fed_dp_lp.p2_pilot import candidate_arrays, metric_masks, sparse_cosine_scores
from fed_dp_lp.p3_data import load_p3_graph
from fed_dp_lp.systems import peak_resident_memory_bytes


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER_PATH = ROOT / "configs" / "p3_master_benchmark.json"
CONFIG_PATH = ROOT / "configs" / "p3_external_baselines.json"
SPLIT_AUDIT_PATH = ROOT / "data" / "manifests" / "p3_split_audit.json"
SPLIT_MANIFEST_PATH = ROOT / "data" / "manifests" / "p3_split_manifest.json"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "p3_benchmark"
OUTPUT = ROOT / "results" / "p3_central_pair_validation"
STREAM = 33001


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def ranking_metrics(labels, scores, masks):
    return {
        scope: {
            "roc_auc": roc_auc(labels[mask], scores[mask]),
            "average_precision": average_precision(labels[mask], scores[mask]),
        }
        for scope, mask in masks.items()
    }


def evaluate(
    *, dataset_index, dataset, seed, epsilon, epsilon_index, dimension,
    learning_rate, train_design, train_labels, validation_design,
    validation_labels, masks, public_scores, train_positive_count, master,
    baseline, commit, role,
):
    sensitivity = EDGE_RECORD_MULTIPLICITY * baseline["clip_norm"]
    private = calibrate_gaussian(
        target_epsilon=epsilon,
        delta=master["privacy"]["delta"],
        sensitivity=sensitivity,
        steps=baseline["steps"],
        orders=DEFAULT_ORDERS,
    )
    rng = np.random.default_rng(
        np.random.SeedSequence(
            [STREAM, dataset_index, seed, epsilon_index, dimension,
             int(round(learning_rate * 1000))]
        )
    )
    started = time.perf_counter()
    weights = train_private_logistic(
        train_design,
        train_labels,
        steps=baseline["steps"],
        learning_rate=learning_rate,
        clip_norm=baseline["clip_norm"],
        noise_std=private.noise_std,
        l2_penalty=baseline["l2_penalty"],
        rng=rng,
    )
    scores = validation_design @ weights
    elapsed = time.perf_counter() - started
    scalar_bytes = np.dtype(np.float64).itemsize
    return {
        "protocol": "P3_2_CENTRAL_PAIR_VALIDATION_v1",
        "role": role,
        "baseline_label": "centralized edge-DP public-pair classifier",
        "official_dplp_reproduction": False,
        "privacy_scope_match": False,
        "scope_mismatch": "centralized trusted curator vs visible federated messages",
        "code_commit": commit,
        "dataset": dataset,
        "seed": seed,
        "epsilon_target": epsilon,
        "split": "validation",
        "test_accessed": False,
        "master_config_sha256": sha256(MASTER_PATH),
        "external_config_sha256": sha256(CONFIG_PATH),
        "split_manifest_sha256": sha256(SPLIT_MANIFEST_PATH),
        "privacy": asdict(private),
        "adjacency": "add_remove_one_canonical_undirected_edge",
        "edge_record_multiplicity": EDGE_RECORD_MULTIPLICITY,
        "l2_sensitivity_per_step": sensitivity,
        "steps": baseline["steps"],
        "projection_dimension": dimension,
        "pair_design_dimension": train_design.shape[1],
        "learning_rate": learning_rate,
        "train_positive_count": train_positive_count,
        "train_negative_count": int(len(train_labels) - train_positive_count),
        "release_dimension": len(weights),
        "client_message_bytes": 0,
        "server_release_bytes": len(weights) * scalar_bytes,
        "wall_time_seconds": elapsed,
        "peak_resident_memory_bytes": peak_resident_memory_bytes(),
        "metrics": {
            "central_pair_dp": ranking_metrics(
                validation_labels, scores, masks
            ),
            "public_cosine": ranking_metrics(
                validation_labels, public_scores, masks
            ),
        },
    }


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def main():
    if OUTPUT.exists():
        raise SystemExit("P3.2 central-pair output exists; refusing overwrite")
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    baseline = config["closest_centralized_edge_dp_lp"]
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("P3 split audit is not clean")
    selection_epsilon = float(baseline["selection_epsilon"])
    selection_index = master["privacy"]["epsilon_grid"].index(selection_epsilon)
    commit = git_head()
    grid_records, curve_records, selections = [], [], {}

    for dataset_index, dataset in enumerate(master["datasets"]):
        graph = load_p3_graph(RAW, dataset)
        with np.load(PROCESSED / dataset / "public_layout.npz") as source:
            homes = source["homes"]
        encodings = {
            dimension: public_svd_encoder(
                graph.public_features,
                dimension=dimension,
                random_state=20260730 + dimension,
            )
            for dimension in baseline["projection_dimensions"]
        }
        development = {}
        for seed in master["split"]["seeds"]:
            with np.load(
                PROCESSED / dataset / f"seed_{seed}_development.npz",
                allow_pickle=False,
            ) as source:
                train_positive = source["train_positive"]
                positive = source["validation_positive"]
                negative = source["validation_negative"]
            train_negative = stable_negative_pairs(
                graph.public_features.shape[0],
                train_positive,
                count=len(train_positive),
                seed=seed + 20260731,
            )
            train_pairs = np.row_stack([train_positive, train_negative])
            train_labels = np.concatenate(
                [np.ones(len(train_positive)), np.zeros(len(train_negative))]
            )
            validation_pairs, validation_labels = candidate_arrays(positive, negative)
            development[seed] = {
                "train_positive_count": len(train_positive),
                "train_labels": train_labels,
                "validation_labels": validation_labels,
                "masks": metric_masks(validation_pairs, homes),
                "public_scores": sparse_cosine_scores(
                    graph.public_features, validation_pairs
                ),
                "train_designs": {
                    dimension: bounded_pair_design(encoded, train_pairs)
                    for dimension, encoded in encodings.items()
                },
                "validation_designs": {
                    dimension: bounded_pair_design(encoded, validation_pairs)
                    for dimension, encoded in encodings.items()
                },
            }
            common = development[seed]
            for dimension in baseline["projection_dimensions"]:
                for learning_rate in baseline["learning_rates"]:
                    grid_records.append(evaluate(
                        dataset_index=dataset_index, dataset=dataset, seed=seed,
                        epsilon=selection_epsilon, epsilon_index=selection_index,
                        dimension=dimension, learning_rate=learning_rate,
                        train_design=common["train_designs"][dimension],
                        validation_design=common["validation_designs"][dimension],
                        train_labels=common["train_labels"],
                        validation_labels=common["validation_labels"],
                        masks=common["masks"], public_scores=common["public_scores"],
                        train_positive_count=common["train_positive_count"],
                        master=master, baseline=baseline, commit=commit,
                        role="validation_grid_at_epsilon_4",
                    ))

        candidates = []
        for dimension in baseline["projection_dimensions"]:
            for learning_rate in baseline["learning_rates"]:
                values = [
                    record["metrics"]["central_pair_dp"]["global"]["roc_auc"]
                    for record in grid_records
                    if record["dataset"] == dataset
                    and record["projection_dimension"] == dimension
                    and record["learning_rate"] == learning_rate
                ]
                candidates.append({
                    "projection_dimension": dimension,
                    "learning_rate": learning_rate,
                    "mean_global_roc_auc": float(np.mean(values)),
                })
        selected = sorted(
            candidates,
            key=lambda item: (-item["mean_global_roc_auc"],
                              item["projection_dimension"],
                              item["learning_rate"]),
        )[0]
        selections[dataset] = {"selected": selected, "grid": candidates}
        for epsilon_index, epsilon in enumerate(master["privacy"]["epsilon_grid"]):
            for seed in master["split"]["seeds"]:
                common = development[seed]
                matching = [
                    record for record in grid_records
                    if float(epsilon) == selection_epsilon
                    and record["dataset"] == dataset and record["seed"] == seed
                    and record["projection_dimension"] == selected["projection_dimension"]
                    and record["learning_rate"] == selected["learning_rate"]
                ]
                if matching:
                    record = dict(matching[0])
                    record["role"] = "selected_validation_epsilon_curve"
                else:
                    record = evaluate(
                        dataset_index=dataset_index, dataset=dataset, seed=seed,
                        epsilon=float(epsilon), epsilon_index=epsilon_index,
                        dimension=selected["projection_dimension"],
                        learning_rate=selected["learning_rate"],
                        train_design=common["train_designs"][selected["projection_dimension"]],
                        validation_design=common["validation_designs"][selected["projection_dimension"]],
                        train_labels=common["train_labels"],
                        validation_labels=common["validation_labels"],
                        masks=common["masks"], public_scores=common["public_scores"],
                        train_positive_count=common["train_positive_count"],
                        master=master, baseline=baseline, commit=commit,
                        role="selected_validation_epsilon_curve",
                    )
                curve_records.append(record)

    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "grid_records.jsonl", grid_records)
    write_jsonl(OUTPUT / "selected_curve_records.jsonl", curve_records)
    (OUTPUT / "summary.json").write_text(json.dumps({
        "protocol": "P3_2_CENTRAL_PAIR_VALIDATION_v1",
        "baseline_label": "centralized edge-DP public-pair classifier",
        "official_dplp_reproduction": False,
        "privacy_scope_match": False,
        "test_accessed": False,
        "grid_record_count": len(grid_records),
        "curve_record_count": len(curve_records),
        "selections": selections,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
