"""Fail-closed audit of the sealed P5FC split state."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p5fc_fresh_frontier.json"
SOURCE_AUDIT_PATH = ROOT / "data/manifests/p5fc_source_audit.json"
MANIFEST_PATH = ROOT / "data/manifests/p5fc_split_manifest.json"
PROCESSED = ROOT / "data/processed/p5fc_frontier"
SEALED = ROOT / "data/sealed/p5fc_frontier"
OUTPUT = ROOT / "data/manifests/p5fc_split_audit.json"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    records = [
        (dataset["dataset"], split)
        for dataset in manifest["datasets"] for split in dataset["splits"]
    ]
    expected_records = len(config["datasets"]) * len(config["split"]["seeds"])
    development_current = True
    sealed_current = True
    counts_valid = True
    strata_valid = True
    for dataset, split in records:
        seed = split["seed"]
        development = PROCESSED / dataset / f"seed_{seed}_development.npz"
        sealed = SEALED / f"{dataset}_seed_{seed}.fernet"
        development_current = development_current and (
            split["commitments"]["development_file_sha256"] == sha256(development)
        )
        sealed_current = sealed_current and (
            split["commitments"]["sealed_payload_sha256"] == sha256(sealed)
        )
        counts = split["counts"]
        counts_valid = counts_valid and (
            counts["validation_positive"]
            == counts["validation_negative"]
            == config["split"]["validation_positive_cap"]
            and counts["test_positive"]
            == counts["test_negative"]
            == config["split"]["test_positive_cap"]
        )
        for name in (
            "validation_positive_strata", "validation_negative_strata",
            "test_positive_strata", "test_negative_strata",
        ):
            values = counts[name]
            strata_valid = strata_valid and abs(values["intra"] - values["cross"]) <= 1

    dataset_map = {item["dataset"]: item for item in manifest["datasets"]}
    checks = {
        "manifest_complete_unique": len(records) == expected_records
        and len({(dataset, split["seed"]) for dataset, split in records})
        == expected_records,
        "datasets_and_seeds_exact": set(dataset_map) == set(config["datasets"])
        and {split["seed"] for _, split in records} == set(config["split"]["seeds"]),
        "config_and_source_audit_current": manifest["config_sha256"]
        == sha256(CONFIG_PATH)
        and manifest["source_audit_sha256"] == sha256(SOURCE_AUDIT_PATH),
        "test_encrypted_never_accessed": manifest["test_status"]
        == "encrypted_never_accessed"
        and manifest["test_access_count"] == 0,
        "sealing_keys_exist": (SEALED / "test.key").exists()
        and (SEALED / "commitment.key").exists(),
        "development_hashes_current": development_current,
        "sealed_hashes_current": sealed_current,
        "frozen_counts": counts_valid,
        "balanced_strata": strata_valid,
        "balanced_clients": all(
            max(item["client_node_counts"]) - min(item["client_node_counts"]) <= 1
            for item in dataset_map.values()
        ),
    }
    audit = {
        "schema_version": 1,
        "protocol": "P5FC_SPLIT_AUDIT_v1",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "test_access_count": 0,
    }
    OUTPUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
