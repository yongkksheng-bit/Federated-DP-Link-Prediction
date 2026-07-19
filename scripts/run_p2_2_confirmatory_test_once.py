"""Decrypt and evaluate the fixed P2.2 confirmatory test exactly once."""

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
from fed_dp_lp.conditioned_release import (
    conditioned_counts,
    conditioned_log_enrichment,
    public_capacity_layout,
    release_conditioned_counts,
    score_conditioned_pairs,
)
from fed_dp_lp.metrics import paired_summary
from fed_dp_lp.p2_data import load_deezer_europe, load_github_social
from fed_dp_lp.p2_pilot import (
    candidate_arrays,
    evaluate_scores,
    metric_masks,
    sparse_cosine_scores,
)
from fed_dp_lp.p2_sealing import array_commitment


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_2_confirmatory.json"
SOURCE_AUDIT = ROOT / "data" / "manifests" / "p2_2_source_audit.json"
SPLIT_MANIFEST = ROOT / "data" / "manifests" / "p2_2_split_manifest.json"
SPLIT_AUDIT = ROOT / "data" / "manifests" / "p2_2_split_audit.json"
FREEZE = ROOT / "docs" / "P2_2_TEST_FREEZE.md"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "p2_2_confirmatory"
SEALED = ROOT / "data" / "sealed" / "p2_2_confirmatory"
OUTPUT = ROOT / "results" / "p2_2_confirmatory_test"
ACCESS = OUTPUT / "access.json"
CANDIDATE = "conditioned_b8_lambda_0.1"


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def require_clean_worktree() -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True
    )
    if status.strip():
        raise SystemExit("refusing one-time test from a dirty worktree")


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_graph(dataset: str):
    archive = RAW / dataset / f"{dataset}.zip"
    if dataset == "github-social-snap":
        return load_github_social(archive)
    if dataset == "deezer-europe-snap":
        return load_deezer_europe(archive)
    raise ValueError(dataset)


def unseal(dataset: str, seed: int, manifest_record: dict, cipher: Fernet, key: bytes):
    path = SEALED / f"{dataset}_seed_{seed}.fernet"
    token = path.read_bytes()
    if sha256(path) != manifest_record["commitments"]["sealed_payload_sha256"]:
        raise RuntimeError(f"{dataset}/{seed}: sealed payload hash mismatch")
    plaintext = cipher.decrypt(token)
    with np.load(io.BytesIO(plaintext), allow_pickle=False) as payload:
        positive = payload["test_positive"]
        negative = payload["test_negative"]
    if array_commitment(
        key, f"{dataset}|{seed}|test_positive", positive
    ) != manifest_record["commitments"]["test_positive"]:
        raise RuntimeError(f"{dataset}/{seed}: positive commitment mismatch")
    if array_commitment(
        key, f"{dataset}|{seed}|test_negative", negative
    ) != manifest_record["commitments"]["test_negative"]:
        raise RuntimeError(f"{dataset}/{seed}: negative commitment mismatch")
    return positive, negative


def local_counts(train_positive, train_scores, homes, cells, layout, clients):
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


def released_scores(local, public, pairs, cells, layout, config, calibration, seed):
    # Reusing this stream for candidate and zero-signal gives a matched noise draw.
    rng = np.random.default_rng(np.random.SeedSequence([seed, 6401]))
    noisy = release_conditioned_counts(
        local,
        noise_std=calibration.noise_std,
        visibility="visible_messages",
        rng=rng,
    )
    residual = conditioned_log_enrichment(
        noisy,
        layout,
        alpha=config["candidate"]["dirichlet_alpha"],
        clip=config["candidate"]["log_enrichment_clip"],
    )
    return score_conditioned_pairs(
        public,
        pairs,
        cells,
        residual,
        layout,
        weight=config["candidate"]["residual_weight"],
    )


def run_dataset(
    dataset, config, calibration, commit, manifest_record, cipher, commitment_key
):
    graph = load_graph(dataset)
    local_dir = PROCESSED / dataset
    with np.load(local_dir / "public_layout.npz", allow_pickle=False) as source:
        homes, cells = source["homes"], source["cells"]
    layout = public_capacity_layout(
        graph.public_features,
        cells,
        np.asarray(config["candidate"]["bin_edges"]),
        maximum_pairs=config["candidate"]["public_capacity_sample_maximum"],
        seed=config["candidate"]["public_capacity_seed"],
        dirichlet_alpha=config["candidate"]["dirichlet_alpha"],
    )
    split_records = {item["seed"]: item for item in manifest_record["splits"]}
    records = []
    for seed in config["split"]["seeds"]:
        with np.load(
            local_dir / f"seed_{seed}_development.npz", allow_pickle=False
        ) as source:
            train_positive = source["train_positive"]
        positive, negative = unseal(
            dataset, seed, split_records[seed], cipher, commitment_key
        )
        pairs, labels = candidate_arrays(positive, negative)
        masks = metric_masks(pairs, homes)
        public = sparse_cosine_scores(graph.public_features, pairs)
        train_scores = sparse_cosine_scores(graph.public_features, train_positive)
        local = local_counts(
            train_positive,
            train_scores,
            homes,
            cells,
            layout,
            config["clients"],
        )
        empty = tuple(np.zeros(layout.dimension) for _ in local)
        random_rng = np.random.default_rng(np.random.SeedSequence([seed, 6201]))
        methods = {
            "public_cosine": public,
            "random_score": random_rng.random(len(pairs)),
            "zero_private_signal": released_scores(
                empty, public, pairs, cells, layout, config, calibration, seed
            ),
            CANDIDATE: released_scores(
                local, public, pairs, cells, layout, config, calibration, seed
            ),
        }
        records.append(
            {
                "protocol": "P2_2_CONFIRMATORY_TEST_v1",
                "code_commit": commit,
                "dataset": dataset,
                "seed": seed,
                "split": "test",
                "test_accessed": True,
                "config_sha256": sha256(CONFIG),
                "source_audit_sha256": sha256(SOURCE_AUDIT),
                "split_manifest_sha256": sha256(SPLIT_MANIFEST),
                "split_audit_sha256": sha256(SPLIT_AUDIT),
                "test_freeze_sha256": sha256(FREEZE),
                "privacy": asdict(calibration),
                "release_dimension": layout.dimension,
                "l2_sensitivity": 1.0,
                "client_count": config["clients"],
                "client_node_counts": np.bincount(
                    homes, minlength=config["clients"]
                ).tolist(),
                "client_train_edge_counts": [int(np.sum(value)) for value in local],
                "candidate_counts": {
                    "positive": len(positive),
                    "negative": len(negative),
                    "intra": int(np.sum(masks["intra"])),
                    "cross": int(np.sum(masks["cross"])),
                },
                "metrics": {
                    name: evaluate_scores(labels, scores, masks)
                    for name, scores in methods.items()
                },
            }
        )
    return records


def summarize(records: list[dict], config: dict) -> dict:
    cells = {}
    all_gates = []
    for dataset in config["datasets"]:
        subset = [record for record in records if record["dataset"] == dataset]
        for metric in ("global", "cross"):
            observed = np.asarray(
                [record["metrics"][CANDIDATE][metric] for record in subset]
            )
            comparisons = {}
            for reference_name in ("public_cosine", "zero_private_signal", "random_score"):
                reference = np.asarray(
                    [record["metrics"][reference_name][metric] for record in subset]
                )
                comparisons[reference_name] = paired_summary(observed, reference)
            public = comparisons["public_cosine"]
            gates = {
                "mean_public_gain_ge_0p02": public["mean_difference"] >= 0.02,
                "public_ci_low_gt_zero": public["ci95_low"] > 0.0,
                "zero_signal_ci_low_gt_zero": comparisons["zero_private_signal"][
                    "ci95_low"
                ]
                > 0.0,
                "random_ci_low_gt_zero": comparisons["random_score"]["ci95_low"]
                > 0.0,
            }
            all_gates.extend(gates.values())
            cells[f"{dataset}/{metric}"] = {
                "candidate_mean": float(np.mean(observed)),
                "comparisons": comparisons,
                "gates": gates,
                "pass": all(gates.values()),
            }
    provenance = {
        "ten_records": len(records) == 10,
        "all_test_records": all(record["test_accessed"] for record in records),
        "dimension_1088": all(record["release_dimension"] == 1088 for record in records),
        "sensitivity_one": all(record["l2_sensitivity"] == 1.0 for record in records),
    }
    all_gates.extend(provenance.values())
    return {
        "protocol": "P2_2_CONFIRMATORY_TEST_v1",
        "candidate": CANDIDATE,
        "test_accessed": True,
        "provenance_checks": provenance,
        "cells": cells,
        "decision": "GO_TO_P3" if all(all_gates) else "NO_GO",
    }


def write_access(payload: dict) -> None:
    ACCESS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    require_clean_worktree()
    if ACCESS.exists() or OUTPUT.exists():
        raise SystemExit("P2.2 test state exists; a second execution is forbidden")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT.read_text(encoding="utf-8"))
    if not FREEZE.exists():
        raise SystemExit("test-freeze document is missing")
    if (
        manifest["test_status"] != "encrypted_never_accessed"
        or manifest["test_access_count"] != 0
        or split_audit["status"] != "PASS"
        or split_audit["test_decrypted"]
    ):
        raise SystemExit("split state is not untouched and audited")
    OUTPUT.mkdir(parents=True)
    commit = git_head()
    access = {
        "schema_version": 1,
        "status": "started",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": commit,
        "config_sha256": sha256(CONFIG),
        "source_audit_sha256": sha256(SOURCE_AUDIT),
        "split_manifest_sha256": sha256(SPLIT_MANIFEST),
        "split_audit_sha256": sha256(SPLIT_AUDIT),
        "test_freeze_sha256": sha256(FREEZE),
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
        manifest_records = {
            record["dataset"]: record for record in manifest["datasets"]
        }
        records = []
        for dataset in config["datasets"]:
            records.extend(
                run_dataset(
                    dataset,
                    config,
                    calibration,
                    commit,
                    manifest_records[dataset],
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
