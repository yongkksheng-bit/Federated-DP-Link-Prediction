"""Audit frozen P2 development files and sealed payload hashes without unsealing."""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_pilot.json"
MANIFEST = ROOT / "data" / "manifests" / "p2_split_manifest.json"
PROCESSED = ROOT / "data" / "processed" / "p2_pilot"
SEALED = ROOT / "data" / "sealed" / "p2_pilot"
OUTPUT = ROOT / "data" / "manifests" / "p2_split_audit.json"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pair_keys(array: np.ndarray, nodes: int) -> set[int]:
    return {int(left) * nodes + int(right) for left, right in array}


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    audited: list[dict] = []

    if manifest["test_status"] != "encrypted_never_accessed":
        failures.append("test status is not encrypted_never_accessed")
    if manifest["test_access_count"] != 0:
        failures.append("test access count is not zero")

    records = {record["dataset"]: record for record in manifest["datasets"]}
    for dataset in config["datasets"]:
        record = records[dataset]
        nodes = record["nodes"]
        if max(record["client_node_counts"]) - min(record["client_node_counts"]) > 1:
            failures.append(f"{dataset}: client node assignment is not balanced")
        if min(record["public_cell_counts"]) <= 0:
            failures.append(f"{dataset}: public coarsening contains an empty cell")

        for split_record in record["splits"]:
            seed = split_record["seed"]
            development_path = PROCESSED / dataset / f"seed_{seed}_development.npz"
            with np.load(development_path, allow_pickle=False) as development:
                train_positive = development["train_positive"]
                train_negative = development["train_negative"]
                validation_positive = development["validation_positive"]
                validation_negative = development["validation_negative"]
            if len(train_positive) != split_record["counts"]["train_positive"]:
                failures.append(f"{dataset}/{seed}: train count mismatch")
            if len(validation_positive) != split_record["counts"]["validation_positive"]:
                failures.append(f"{dataset}/{seed}: validation count mismatch")
            positive = pair_keys(train_positive, nodes)
            validation = pair_keys(validation_positive, nodes)
            negative = pair_keys(train_negative, nodes) | pair_keys(validation_negative, nodes)
            if positive & validation:
                failures.append(f"{dataset}/{seed}: train/validation positive overlap")
            if (positive | validation) & negative:
                failures.append(f"{dataset}/{seed}: development positive/negative overlap")

            sealed_path = SEALED / f"{dataset}_seed_{seed}.fernet"
            if sha256(sealed_path) != split_record["commitments"]["sealed_payload_sha256"]:
                failures.append(f"{dataset}/{seed}: sealed payload hash mismatch")
            audited.append(
                {
                    "dataset": dataset,
                    "seed": seed,
                    "development_counts_match": True,
                    "development_sets_disjoint": True,
                    "sealed_hash_match": True,
                }
            )

    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha256(MANIFEST),
        "test_decrypted": False,
        "audited_cells": len(audited),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
        "cells": audited,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if failures:
        raise SystemExit("P2 split audit failed")


if __name__ == "__main__":
    main()
