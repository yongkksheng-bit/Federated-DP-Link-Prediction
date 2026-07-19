"""Audit P3 development arrays and sealed payload hashes without decrypting."""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p3_master_benchmark.json"
MANIFEST = ROOT / "data" / "manifests" / "p3_split_manifest.json"
PROCESSED = ROOT / "data" / "processed" / "p3_benchmark"
SEALED = ROOT / "data" / "sealed" / "p3_benchmark"
OUTPUT = ROOT / "data" / "manifests" / "p3_split_audit.json"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair_keys(array: np.ndarray, nodes: int) -> set[int]:
    return {int(left) * nodes + int(right) for left, right in array}


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("P3 split audit exists; refusing overwrite")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = []
    cells = []
    if manifest["test_status"] != "encrypted_never_accessed":
        failures.append("test status changed")
    if manifest["test_access_count"] != 0:
        failures.append("test access count is nonzero")
    records = {record["dataset"]: record for record in manifest["datasets"]}
    for dataset in config["datasets"]:
        record = records[dataset]
        if max(record["client_node_counts"]) - min(record["client_node_counts"]) > 1:
            failures.append(f"{dataset}: unbalanced clients")
        if len(record["public_cell_counts"]) != 16 or min(record["public_cell_counts"]) < 2:
            failures.append(f"{dataset}: invalid public cells")
        for split in record["splits"]:
            seed = split["seed"]
            with np.load(
                PROCESSED / dataset / f"seed_{seed}_development.npz",
                allow_pickle=False,
            ) as data:
                train_positive = data["train_positive"]
                train_negative = data["train_negative"]
                validation_positive = data["validation_positive"]
                validation_negative = data["validation_negative"]
            positive_train = pair_keys(train_positive, record["nodes"])
            positive_validation = pair_keys(validation_positive, record["nodes"])
            negative_train = pair_keys(train_negative, record["nodes"])
            negative_validation = pair_keys(validation_negative, record["nodes"])
            if positive_train & positive_validation:
                failures.append(f"{dataset}/{seed}: positive overlap")
            if (positive_train | positive_validation) & (
                negative_train | negative_validation
            ):
                failures.append(f"{dataset}/{seed}: positive-negative overlap")
            if negative_train & negative_validation:
                failures.append(f"{dataset}/{seed}: negative overlap")
            sealed = SEALED / f"{dataset}_seed_{seed}.fernet"
            hash_match = sha256(sealed) == split["commitments"][
                "sealed_payload_sha256"
            ]
            if not hash_match:
                failures.append(f"{dataset}/{seed}: sealed hash mismatch")
            cells.append(
                {"dataset": dataset, "seed": seed, "sealed_hash_match": hash_match}
            )
    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha256(MANIFEST),
        "test_decrypted": False,
        "audited_cells": len(cells),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
        "cells": cells,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if failures:
        raise SystemExit("P3 split audit failed")


if __name__ == "__main__":
    main()
