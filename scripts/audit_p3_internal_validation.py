"""Audit P3.1 completeness, privacy calibration, dimensions, and test state."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np

from fed_dp_lp.systems import logical_payload_bytes


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER = ROOT / "configs" / "p3_master_benchmark.json"
CONFIG = ROOT / "configs" / "p3_internal_validation.json"
SOURCE = ROOT / "data" / "manifests" / "p3_source_contract.json"
SPLIT = ROOT / "data" / "manifests" / "p3_split_manifest.json"
SPLIT_AUDIT = ROOT / "data" / "manifests" / "p3_split_audit.json"
RESULTS = ROOT / "results" / "p3_internal_validation"
OUTPUT = RESULTS / "audit.json"
EXPECTED_COMMIT = "61ddb4bbb2149e0b2cb3bdb5023e99cee8baf0c1"
DIMENSIONS = {
    "dp_unconditioned_b1_visible_messages": 136,
    "dp_conditioned_b4_visible_messages": 544,
    "dp_conditioned_b8_visible_messages": 1088,
    "matched_zero_private_signal_b8_visible": 1088,
    "dp_conditioned_b8_ideal_secagg": 1088,
    "nonprivate_conditioned_b8_reference": 1088,
    "public_cosine": 0,
    "random_score": 0,
}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("P3.1 audit exists; refusing overwrite")
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT.read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in (RESULTS / "records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    failures = []
    expected_cells = {
        (dataset, seed, float(epsilon))
        for dataset in master["datasets"]
        for seed in master["split"]["seeds"]
        for epsilon in master["privacy"]["epsilon_grid"]
    }
    observed_cells = {
        (record["dataset"], record["seed"], float(record["epsilon_target"]))
        for record in records
    }
    if observed_cells != expected_cells or len(records) != len(expected_cells):
        failures.append("record grid is incomplete or duplicated")
    expected_hashes = {
        "master_config_sha256": sha256(MASTER),
        "validation_config_sha256": sha256(CONFIG),
        "source_contract_sha256": sha256(SOURCE),
        "split_manifest_sha256": sha256(SPLIT),
        "split_audit_sha256": sha256(SPLIT_AUDIT),
    }
    for index, record in enumerate(records):
        label = f"{record['dataset']}/{record['seed']}/{record['epsilon_target']}"
        if record["code_commit"] != EXPECTED_COMMIT:
            failures.append(f"{label}: code commit mismatch")
        if record["test_accessed"] or record["split"] != "validation":
            failures.append(f"{label}: invalid access/split state")
        if record["l2_sensitivity"] != 1.0:
            failures.append(f"{label}: sensitivity mismatch")
        for key, expected in expected_hashes.items():
            if record[key] != expected:
                failures.append(f"{label}: {key} mismatch")
        target = float(record["epsilon_target"])
        if record["privacy"]["epsilon"] > target + 1e-8:
            failures.append(f"{label}: calibrated epsilon exceeds target")
        if record["privacy"]["delta"] != master["privacy"]["delta"]:
            failures.append(f"{label}: delta mismatch")
        if set(record["metrics"]) != set(config["methods_per_epsilon"]):
            failures.append(f"{label}: method set mismatch")
        for method, dimension in DIMENSIONS.items():
            system = record["systems"][method]
            if system["release_dimension"] != dimension:
                failures.append(f"{label}/{method}: dimension mismatch")
            expected_payload = (
                logical_payload_bytes(clients=master["clients"], dimension=dimension)
                if dimension
                else {"client_payload_bytes": 0, "server_release_bytes": 0}
            )
            for key, expected in expected_payload.items():
                if system[key] != expected:
                    failures.append(f"{label}/{method}: {key} mismatch")
            if system["wall_time_seconds"] < 0:
                failures.append(f"{label}/{method}: negative wall time")
        if record["peak_resident_memory_bytes"] <= 0:
            failures.append(f"{label}: invalid peak memory")
        values = [
            value
            for method in record["metrics"].values()
            for scope in method.values()
            for value in scope.values()
        ]
        if not np.all(np.isfinite(values)):
            failures.append(f"{label}: nonfinite metric")
    if split["test_access_count"] != 0 or split["test_status"] != "encrypted_never_accessed":
        failures.append("P3 split manifest is no longer untouched")
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        failures.append("P3 split audit is not clean")
    payload = {
        "schema_version": 1,
        "records_sha256": sha256(RESULTS / "records.jsonl"),
        "summary_sha256": sha256(RESULTS / "summary.json"),
        "audited_records": len(records),
        "expected_cells": len(expected_cells),
        "test_decrypted": False,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))
    if failures:
        raise SystemExit("P3.1 validation audit failed")


if __name__ == "__main__":
    main()
