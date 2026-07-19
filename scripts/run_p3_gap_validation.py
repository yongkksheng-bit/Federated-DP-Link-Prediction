"""Validate the frozen GAP-style LP adaptation without accessing P3 test."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import time
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.gap_adaptation import (
    UNDIRECTED_EDGE_L2_SENSITIVITY,
    client_owned_edges,
    public_svd_encoder,
    release_private_aggregations,
    score_pairs_from_channels,
    undirected_adjacency,
)
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
OUTPUT = ROOT / "results" / "p3_gap_validation"
STREAM = 32001


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
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


def calibration(master, epsilon, hops):
    return calibrate_gaussian(
        target_epsilon=epsilon,
        delta=master["privacy"]["delta"],
        sensitivity=UNDIRECTED_EDGE_L2_SENSITIVITY,
        steps=hops,
        orders=DEFAULT_ORDERS,
    )


def evaluate(
    *,
    dataset_index,
    dataset,
    seed,
    epsilon,
    epsilon_index,
    dimension,
    hops,
    encoded,
    local_edges,
    adjacency,
    pairs,
    labels,
    masks,
    public_scores,
    clients,
    master,
    commit,
    role,
):
    private = calibration(master, epsilon, hops)
    started = time.perf_counter()
    rng = np.random.default_rng(
        np.random.SeedSequence(
            [STREAM, dataset_index, seed, epsilon_index, dimension, hops]
        )
    )
    channels = release_private_aggregations(
        local_edges,
        encoded,
        hops=hops,
        noise_std=private.noise_std,
        visibility="visible_messages",
        rng=rng,
        adjacency=adjacency,
    )
    scores = score_pairs_from_channels(channels, pairs)
    elapsed = time.perf_counter() - started
    release_dimension = hops * encoded.shape[0] * encoded.shape[1]
    scalar_bytes = np.dtype(np.float64).itemsize
    return {
        "protocol": "P3_2_GAP_STYLE_VALIDATION_v1",
        "role": role,
        "baseline_label": "GAP-style inference-closed LP adaptation",
        "official_reproduction": False,
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
        "l2_sensitivity_per_hop": UNDIRECTED_EDGE_L2_SENSITIVITY,
        "hops": hops,
        "projection_dimension_requested": dimension,
        "projection_dimension": encoded.shape[1],
        "visibility": "individually_visible_client_messages",
        "server_sum_simulation": "distribution_equivalent_sqrt_K_gaussian",
        "client_count": clients,
        "client_train_edge_counts": [len(edges) for edges in local_edges],
        "release_dimension": release_dimension,
        "client_message_bytes": clients * release_dimension * scalar_bytes,
        "server_release_bytes": release_dimension * scalar_bytes,
        "wall_time_seconds": elapsed,
        "peak_resident_memory_bytes": peak_resident_memory_bytes(),
        "metrics": {
            "gap_style_lp": ranking_metrics(labels, scores, masks),
            "public_cosine": ranking_metrics(labels, public_scores, masks),
        },
    }


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def main():
    if OUTPUT.exists():
        raise SystemExit("P3.2 GAP output exists; refusing overwrite")
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("P3 split audit is not clean")
    gap = config["gap_style_lp"]
    selection_epsilon = float(gap["selection_epsilon"])
    selection_index = master["privacy"]["epsilon_grid"].index(selection_epsilon)
    commit = git_head()
    grid_records = []
    curve_records = []
    selections = {}

    for dataset_index, dataset in enumerate(master["datasets"]):
        graph = load_p3_graph(RAW, dataset)
        with np.load(
            PROCESSED / dataset / "public_layout.npz", allow_pickle=False
        ) as source:
            homes = source["homes"]
        encodings = {
            dimension: public_svd_encoder(
                graph.public_features,
                dimension=dimension,
                random_state=20260724 + dimension,
            )
            for dimension in gap["projection_dimensions"]
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
            pairs, labels = candidate_arrays(positive, negative)
            development[seed] = {
                "local_edges": client_owned_edges(
                    train_positive, homes, clients=master["clients"]
                ),
                "pairs": pairs,
                "labels": labels,
                "masks": metric_masks(pairs, homes),
                "public_scores": sparse_cosine_scores(graph.public_features, pairs),
            }
            development[seed]["adjacency"] = undirected_adjacency(
                development[seed]["local_edges"], graph.public_features.shape[0]
            )
            for dimension, encoded in encodings.items():
                for hops in gap["hops"]:
                    grid_records.append(
                        evaluate(
                            dataset_index=dataset_index,
                            dataset=dataset,
                            seed=seed,
                            epsilon=selection_epsilon,
                            epsilon_index=selection_index,
                            dimension=dimension,
                            hops=hops,
                            encoded=encoded,
                            clients=master["clients"],
                            master=master,
                            commit=commit,
                            role="validation_grid_at_epsilon_4",
                            **development[seed],
                        )
                    )

        candidates = []
        for dimension in gap["projection_dimensions"]:
            for hops in gap["hops"]:
                values = [
                    record["metrics"]["gap_style_lp"]["global"]["roc_auc"]
                    for record in grid_records
                    if record["dataset"] == dataset
                    and record["projection_dimension_requested"] == dimension
                    and record["hops"] == hops
                ]
                candidates.append(
                    {
                        "projection_dimension": dimension,
                        "hops": hops,
                        "mean_global_roc_auc": float(np.mean(values)),
                    }
                )
        selected = sorted(
            candidates,
            key=lambda item: (
                -item["mean_global_roc_auc"],
                item["hops"],
                item["projection_dimension"],
            ),
        )[0]
        selections[dataset] = {"selected": selected, "grid": candidates}
        for epsilon_index, epsilon in enumerate(master["privacy"]["epsilon_grid"]):
            for seed in master["split"]["seeds"]:
                curve_records.append(
                    evaluate(
                        dataset_index=dataset_index,
                        dataset=dataset,
                        seed=seed,
                        epsilon=float(epsilon),
                        epsilon_index=epsilon_index,
                        dimension=selected["projection_dimension"],
                        hops=selected["hops"],
                        encoded=encodings[selected["projection_dimension"]],
                        clients=master["clients"],
                        master=master,
                        commit=commit,
                        role="selected_validation_epsilon_curve",
                        **development[seed],
                    )
                )

    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "grid_records.jsonl", grid_records)
    write_jsonl(OUTPUT / "selected_curve_records.jsonl", curve_records)
    summary = {
        "protocol": "P3_2_GAP_STYLE_VALIDATION_v1",
        "baseline_label": "GAP-style inference-closed LP adaptation",
        "official_reproduction": False,
        "test_accessed": False,
        "grid_record_count": len(grid_records),
        "curve_record_count": len(curve_records),
        "selections": selections,
    }
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
