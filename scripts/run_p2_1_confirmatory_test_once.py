"""Decrypt and evaluate the P2.1 confirmatory test exactly once."""

from __future__ import annotations

import hashlib
import io
import json
import pathlib
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone

import numpy as np
from cryptography.fernet import Fernet

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.block_release import block_counts, make_block_layout, release_block_densities
from fed_dp_lp.metrics import paired_summary
from fed_dp_lp.p2_data import load_lastfm, load_polblogs
from fed_dp_lp.p2_pilot import candidate_arrays, evaluate_scores, metric_masks, sparse_cosine_scores
from fed_dp_lp.p2_sealing import array_commitment
from fed_dp_lp.public_views import repartition_edges
from fed_dp_lp.residual_release import residual_map, score_with_residual


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_1_confirmatory.json"
MANIFEST = ROOT / "data" / "manifests" / "p2_1_split_manifest.json"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "p2_1_confirmatory"
SEALED = ROOT / "data" / "sealed" / "p2_1_confirmatory"
OUTPUT = ROOT / "results" / "p2_1_confirmatory_test"
ACCESS = OUTPUT / "access.json"


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph_for(dataset: str):
    archive = RAW / dataset / f"{dataset}.zip"
    return load_polblogs(archive) if dataset == "polblogs-newman" else load_lastfm(archive)


def release_scores(client_edges, cells, pairs, public, calibration, seed, visibility, stream):
    rng = np.random.default_rng(np.random.SeedSequence([seed, stream]))
    counts, _, layout = release_block_densities(
        client_edges,
        cells,
        noise_std=calibration.noise_std,
        visibility=visibility,
        rng=rng,
    )
    residuals = residual_map(counts, layout, transform="centered_block_rank")
    return score_with_residual(public, pairs, cells, residuals, layout, weight=0.05)


def unseal(dataset: str, seed: int, manifest_record: dict, cipher: Fernet, key: bytes):
    path = SEALED / f"{dataset}_seed_{seed}.fernet"
    token = path.read_bytes()
    if hashlib.sha256(token).hexdigest() != manifest_record["commitments"][
        "sealed_payload_sha256"
    ]:
        raise RuntimeError(f"{dataset}/{seed}: sealed payload hash mismatch")
    plaintext = cipher.decrypt(token)
    with np.load(io.BytesIO(plaintext), allow_pickle=False) as payload:
        positive = payload["test_positive"]
        negative = payload["test_negative"]
    expected_positive = array_commitment(
        key, f"{dataset}|{seed}|test_positive", positive
    )
    expected_negative = array_commitment(
        key, f"{dataset}|{seed}|test_negative", negative
    )
    if expected_positive != manifest_record["commitments"]["test_positive"]:
        raise RuntimeError(f"{dataset}/{seed}: positive commitment mismatch")
    if expected_negative != manifest_record["commitments"]["test_negative"]:
        raise RuntimeError(f"{dataset}/{seed}: negative commitment mismatch")
    return positive, negative


def run_record(dataset, seed, split_record, config, calibration, commit, cipher, key):
    graph = graph_for(dataset)
    with np.load(PROCESSED / dataset / "public_layout.npz", allow_pickle=False) as source:
        homes, cells = source["homes"], source["cells"]
    with np.load(
        PROCESSED / dataset / f"seed_{seed}_development.npz", allow_pickle=False
    ) as source:
        train_positive = source["train_positive"]
    positive, negative = unseal(dataset, seed, split_record, cipher, key)
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
    random_rng = np.random.default_rng(np.random.SeedSequence([seed, 3001]))
    scores = {
        "public_cosine": public,
        "random_score": random_rng.random(len(pairs)),
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
        "protocol": "P2_1_CONFIRMATORY_TEST_v1",
        "code_commit": commit,
        "dataset": dataset,
        "seed": seed,
        "split": "test",
        "test_accessed": True,
        "config_sha256": sha256(CONFIG),
        "split_manifest_sha256": sha256(MANIFEST),
        "privacy": asdict(calibration),
        "release_dimension": layout.dimension,
        "l2_sensitivity": 1.0,
        "client_count": len(clients),
        "client_node_counts": np.bincount(homes, minlength=len(clients)).tolist(),
        "client_train_edge_counts": [len(edges) for edges in clients],
        "candidate_counts": {
            "positive": len(positive),
            "negative": len(negative),
            "intra": int(masks["intra"].sum()),
            "cross": int(masks["cross"].sum()),
        },
        "metrics": {
            method: evaluate_scores(labels, values, masks) for method, values in scores.items()
        },
    }


def summarize(records: list[dict], config: dict) -> dict:
    candidate = "public_cosine_plus_dp_residual_visible_messages"
    cells = {}
    all_pass = []
    for dataset in config["datasets"]:
        subset = [record for record in records if record["dataset"] == dataset]
        for metric in ("global", "cross"):
            observed = np.asarray([r["metrics"][candidate][metric] for r in subset])
            comparisons = {}
            for reference in (
                "public_cosine",
                "public_cosine_plus_zero_private_noise",
                "random_score",
            ):
                baseline = np.asarray([r["metrics"][reference][metric] for r in subset])
                comparisons[reference] = paired_summary(observed, baseline)
            public = comparisons["public_cosine"]
            gates = {
                "mean_public_gain_ge_0p02": public["mean_difference"] >= 0.02,
                "public_ci_low_gt_zero": public["ci95_low"] > 0,
                "zero_signal_ci_low_gt_zero": comparisons[
                    "public_cosine_plus_zero_private_noise"
                ]["ci95_low"]
                > 0,
                "random_ci_low_gt_zero": comparisons["random_score"]["ci95_low"] > 0,
            }
            all_pass.extend(gates.values())
            cells[f"{dataset}/{metric}"] = {
                "candidate_mean": float(np.mean(observed)),
                "comparisons": comparisons,
                "gates": gates,
                "pass": all(gates.values()),
            }
    return {
        "protocol": "P2_1_CONFIRMATORY_TEST_v1",
        "test_accessed": True,
        "cells": cells,
        "decision": "GO_TO_P3" if all(all_pass) else "NO_GO",
    }


def write_access(payload: dict) -> None:
    ACCESS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if ACCESS.exists():
        raise SystemExit("test access record exists; a second execution is forbidden")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["test_status"] != "encrypted_never_accessed" or manifest[
        "test_access_count"
    ] != 0:
        raise SystemExit("split manifest is not in the untouched state")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    commit = git_head()
    access = {
        "schema_version": 1,
        "status": "started",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": commit,
        "config_sha256": sha256(CONFIG),
        "split_manifest_sha256": sha256(MANIFEST),
        "planned_payloads": 10,
    }
    write_access(access)
    try:
        cipher = Fernet((SEALED / "test.key").read_bytes())
        commitment_key = (SEALED / "commitment.key").read_bytes()
        calibration = calibrate_gaussian(
            target_epsilon=config["privacy"]["epsilon"],
            delta=config["privacy"]["delta"],
            sensitivity=config["privacy"]["l2_sensitivity"],
            steps=config["privacy"]["releases"],
            orders=DEFAULT_ORDERS,
        )
        manifest_datasets = {
            record["dataset"]: record for record in manifest["datasets"]
        }
        records = []
        for dataset in config["datasets"]:
            split_records = {
                split["seed"]: split for split in manifest_datasets[dataset]["splits"]
            }
            for seed in config["split"]["seeds"]:
                records.append(
                    run_record(
                        dataset,
                        seed,
                        split_records[seed],
                        config,
                        calibration,
                        commit,
                        cipher,
                        commitment_key,
                    )
                )
        records_path = OUTPUT / "records.jsonl"
        with records_path.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
        summary_path = OUTPUT / "summary.json"
        summary_path.write_text(
            json.dumps(summarize(records, config), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        access.update(
            {
                "status": "completed",
                "completed_utc": datetime.now(timezone.utc).isoformat(),
                "payloads_accessed": len(records),
                "records_sha256": sha256(records_path),
                "summary_sha256": sha256(summary_path),
            }
        )
        write_access(access)
        print(summary_path)
    except Exception as error:
        access.update(
            {
                "status": "failed_after_access_started",
                "failed_utc": datetime.now(timezone.utc).isoformat(),
                "error_type": type(error).__name__,
            }
        )
        write_access(access)
        raise


if __name__ == "__main__":
    main()
