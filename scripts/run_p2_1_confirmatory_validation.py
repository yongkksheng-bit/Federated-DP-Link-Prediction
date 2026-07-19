"""Run the fixed P2.1 method on confirmatory validation splits only."""

from __future__ import annotations

import json
import pathlib
import subprocess
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.block_release import block_counts, make_block_layout, release_block_densities
from fed_dp_lp.metrics import paired_summary
from fed_dp_lp.p2_data import load_lastfm, load_polblogs
from fed_dp_lp.p2_pilot import candidate_arrays, evaluate_scores, metric_masks, sparse_cosine_scores
from fed_dp_lp.public_views import repartition_edges
from fed_dp_lp.residual_release import residual_map, score_with_residual


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_1_confirmatory.json"
GATE = ROOT / "configs" / "p2_1_validation_gate.json"
MANIFEST = ROOT / "data" / "manifests" / "p2_1_split_manifest.json"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "p2_1_confirmatory"
OUTPUT = ROOT / "results" / "p2_1_confirmatory_validation"


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def sha256(path: pathlib.Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph_for(dataset: str):
    archive = RAW / dataset / f"{dataset}.zip"
    return load_polblogs(archive) if dataset == "polblogs-newman" else load_lastfm(archive)


def release_scores(client_edges, cells, pairs, public, calibration, seed, visibility, stream):
    rng = np.random.default_rng(np.random.SeedSequence([seed, stream]))
    noisy_counts, _, layout = release_block_densities(
        client_edges,
        cells,
        noise_std=calibration.noise_std,
        visibility=visibility,
        rng=rng,
    )
    residuals = residual_map(noisy_counts, layout, transform="centered_block_rank")
    return score_with_residual(public, pairs, cells, residuals, layout, weight=0.05)


def run_record(dataset: str, seed: int, config: dict, calibration, commit: str) -> dict:
    graph = graph_for(dataset)
    with np.load(PROCESSED / dataset / "public_layout.npz", allow_pickle=False) as source:
        homes, cells = source["homes"], source["cells"]
    with np.load(
        PROCESSED / dataset / f"seed_{seed}_development.npz", allow_pickle=False
    ) as source:
        train_positive = source["train_positive"]
        positive = source["validation_positive"]
        negative = source["validation_negative"]
    pairs, labels = candidate_arrays(positive, negative)
    masks = metric_masks(pairs, homes)
    public = sparse_cosine_scores(graph.public_features, pairs)
    clients = repartition_edges(train_positive, homes, clients=config["clients"])
    empty = tuple(np.empty((0, 2), dtype=np.int64) for _ in clients)
    layout = make_block_layout(cells)
    nonprivate_counts = sum(
        (block_counts(edges, cells, layout) for edges in clients),
        start=np.zeros(layout.dimension),
    )
    nonprivate_residual = residual_map(
        nonprivate_counts, layout, transform="centered_block_rank"
    )
    rng = np.random.default_rng(np.random.SeedSequence([seed, 3001]))
    scores = {
        "public_cosine": public,
        "random_score": rng.random(len(pairs)),
        "public_cosine_plus_nonprivate_residual": score_with_residual(
            public, pairs, cells, nonprivate_residual, layout, weight=0.05
        ),
        "public_cosine_plus_zero_private_noise": release_scores(
            empty, cells, pairs, public, calibration, seed, "visible_messages", 3101
        ),
        "public_cosine_plus_dp_residual_visible_messages": release_scores(
            clients, cells, pairs, public, calibration, seed, "visible_messages", 3201
        ),
        "public_cosine_plus_dp_residual_ideal_secagg": release_scores(
            clients, cells, pairs, public, calibration, seed, "ideal_secagg", 3301
        ),
    }
    return {
        "protocol": "P2_1_CONFIRMATORY_VALIDATION_v1",
        "code_commit": commit,
        "dataset": dataset,
        "seed": seed,
        "split": "validation",
        "test_accessed": False,
        "config_sha256": sha256(CONFIG),
        "gate_sha256": sha256(GATE),
        "split_manifest_sha256": sha256(MANIFEST),
        "privacy": asdict(calibration),
        "release_dimension": layout.dimension,
        "l2_sensitivity": 1.0,
        "client_count": len(clients),
        "client_node_counts": np.bincount(homes, minlength=len(clients)).tolist(),
        "client_train_edge_counts": [len(edges) for edges in clients],
        "metrics": {
            method: evaluate_scores(labels, values, masks) for method, values in scores.items()
        },
    }


def summarize(records: list[dict], gate: dict) -> dict:
    candidate = gate["candidate"]
    cells = {}
    passes = []
    for dataset in gate["datasets"]:
        subset = [record for record in records if record["dataset"] == dataset]
        for metric in gate["metrics"]:
            observed = np.asarray([r["metrics"][candidate][metric] for r in subset])
            public = np.asarray([r["metrics"]["public_cosine"][metric] for r in subset])
            summary = paired_summary(observed, public)
            summary["candidate_mean"] = float(np.mean(observed))
            summary["public_mean"] = float(np.mean(public))
            summary["validation_advance"] = (
                summary["mean_difference"]
                > gate["advance_rule"]["minimum_mean_gain_over_public_cosine"]
            )
            passes.append(summary["validation_advance"])
            cells[f"{dataset}/{metric}"] = summary
    return {
        "protocol": "P2_1_CONFIRMATORY_VALIDATION_v1",
        "test_accessed": False,
        "cells": cells,
        "decision": "ADVANCE_TO_TEST_FREEZE" if all(passes) else "NO_GO",
    }


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("confirmatory validation already exists; refusing overwrite")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    calibration = calibrate_gaussian(
        target_epsilon=config["privacy"]["epsilon"],
        delta=config["privacy"]["delta"],
        sensitivity=config["privacy"]["l2_sensitivity"],
        steps=config["privacy"]["releases"],
        orders=DEFAULT_ORDERS,
    )
    commit = git_head()
    records = [
        run_record(dataset, seed, config, calibration, commit)
        for dataset in config["datasets"]
        for seed in config["split"]["seeds"]
    ]
    OUTPUT.mkdir(parents=True)
    with (OUTPUT / "records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(
        json.dumps(summarize(records, gate), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
