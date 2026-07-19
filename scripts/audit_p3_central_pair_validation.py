"""Audit the P3.2 centralized formal edge-DP baseline."""

import json
import hashlib
import pathlib

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER = json.loads((ROOT / "configs/p3_master_benchmark.json").read_text())
CONFIG = json.loads((ROOT / "configs/p3_external_baselines.json").read_text())
OUTPUT = ROOT / "results/p3_central_pair_validation"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    grid = read_jsonl(OUTPUT / "grid_records.jsonl")
    curve = read_jsonl(OUTPUT / "selected_curve_records.jsonl")
    summary = json.loads((OUTPUT / "summary.json").read_text())
    baseline = CONFIG["closest_centralized_edge_dp_lp"]
    expected_grid = (len(MASTER["datasets"]) * len(MASTER["split"]["seeds"])
                     * len(baseline["projection_dimensions"])
                     * len(baseline["learning_rates"]))
    expected_curve = (len(MASTER["datasets"]) * len(MASTER["split"]["seeds"])
                      * len(MASTER["privacy"]["epsilon_grid"]))
    records = grid + curve
    checks = {
        "grid_complete": len(grid) == expected_grid,
        "curve_complete": len(curve) == expected_curve,
        "six_dataset_selections": set(summary["selections"]) == set(MASTER["datasets"]),
        "test_never_accessed": not summary["test_accessed"] and all(
            not record["test_accessed"] for record in records),
        "sensitivity_is_3C": all(np.isclose(
            record["l2_sensitivity_per_step"],
            3 * baseline["clip_norm"]) for record in records),
        "complete_rdp": all(len(record["privacy"]["orders"])
                            == len(record["privacy"]["rdp"]) for record in records),
        "scope_mismatch_disclosed": all(
            not record["privacy_scope_match"]
            and not record["official_dplp_reproduction"] for record in records),
        "finite_metrics": all(np.isfinite(value) for record in records
            for method in record["metrics"].values()
            for scope in method.values() for value in scope.values()),
        "config_hash_current": all(
            record["external_config_sha256"]
            == sha256(ROOT / "configs/p3_external_baselines.json")
            for record in records),
    }
    audit = {
        "protocol": "P3_2_CENTRAL_PAIR_VALIDATION_AUDIT_v1",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "test_accessed": False,
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
