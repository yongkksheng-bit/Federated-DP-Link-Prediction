"""Audit P2.1 development files and sealed hashes without decrypting test."""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_1_confirmatory.json"
MANIFEST = ROOT / "data" / "manifests" / "p2_1_split_manifest.json"
PROCESSED = ROOT / "data" / "processed" / "p2_1_confirmatory"
SEALED = ROOT / "data" / "sealed" / "p2_1_confirmatory"
OUTPUT = ROOT / "data" / "manifests" / "p2_1_split_audit.json"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def keys(array: np.ndarray, nodes: int) -> set[int]:
    return {int(left) * nodes + int(right) for left, right in array}


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = []
    audited = []
    if manifest["test_status"] != "encrypted_never_accessed":
        failures.append("test status changed")
    if manifest["test_access_count"] != 0:
        failures.append("test access count is nonzero")
    records = {record["dataset"]: record for record in manifest["datasets"]}
    for dataset in config["datasets"]:
        record = records[dataset]
        if max(record["client_node_counts"]) - min(record["client_node_counts"]) > 1:
            failures.append(f"{dataset}: unbalanced clients")
        if min(record["public_cell_counts"]) < 2:
            failures.append(f"{dataset}: public cell too small for block capacities")
        for split in record["splits"]:
            seed = split["seed"]
            path = PROCESSED / dataset / f"seed_{seed}_development.npz"
            with np.load(path, allow_pickle=False) as data:
                train_positive = data["train_positive"]
                train_negative = data["train_negative"]
                validation_positive = data["validation_positive"]
                validation_negative = data["validation_negative"]
            positive_train = keys(train_positive, record["nodes"])
            positive_validation = keys(validation_positive, record["nodes"])
            negative = keys(train_negative, record["nodes"]) | keys(
                validation_negative, record["nodes"]
            )
            if positive_train & positive_validation:
                failures.append(f"{dataset}/{seed}: positive overlap")
            if (positive_train | positive_validation) & negative:
                failures.append(f"{dataset}/{seed}: positive-negative overlap")
            if len(train_positive) != split["counts"]["train_positive"]:
                failures.append(f"{dataset}/{seed}: train count mismatch")
            if len(validation_positive) != split["counts"]["validation_positive"]:
                failures.append(f"{dataset}/{seed}: validation count mismatch")
            sealed = SEALED / f"{dataset}_seed_{seed}.fernet"
            if sha256(sealed) != split["commitments"]["sealed_payload_sha256"]:
                failures.append(f"{dataset}/{seed}: sealed hash mismatch")
            audited.append({"dataset": dataset, "seed": seed, "sealed_hash_match": True})
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
        raise SystemExit("P2.1 split audit failed")


if __name__ == "__main__":
    main()
