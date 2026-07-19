"""Audit P3.2 GAP-style validation completeness and privacy metadata."""

from __future__ import annotations

import json
import hashlib
import pathlib

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER = json.loads(
    (ROOT / "configs" / "p3_master_benchmark.json").read_text(encoding="utf-8")
)
CONFIG = json.loads(
    (ROOT / "configs" / "p3_external_baselines.json").read_text(encoding="utf-8")
)
OUTPUT = ROOT / "results" / "p3_gap_validation"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    grid = read_jsonl(OUTPUT / "grid_records.jsonl")
    curve = read_jsonl(OUTPUT / "selected_curve_records.jsonl")
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    expected_grid = (
        len(MASTER["datasets"])
        * len(MASTER["split"]["seeds"])
        * len(CONFIG["gap_style_lp"]["projection_dimensions"])
        * len(CONFIG["gap_style_lp"]["hops"])
    )
    expected_curve = (
        len(MASTER["datasets"])
        * len(MASTER["split"]["seeds"])
        * len(MASTER["privacy"]["epsilon_grid"])
    )
    all_records = grid + curve
    checks = {
        "grid_complete": len(grid) == expected_grid,
        "selected_curve_complete": len(curve) == expected_curve,
        "six_dataset_selections": set(summary["selections"]) == set(MASTER["datasets"]),
        "test_never_accessed": not summary["test_accessed"]
        and all(not record["test_accessed"] for record in all_records),
        "undirected_sensitivity_sqrt_two": all(
            np.isclose(record["l2_sensitivity_per_hop"], np.sqrt(2.0))
            for record in all_records
        ),
        "complete_rdp_curves": all(
            len(record["privacy"]["orders"]) == len(record["privacy"]["rdp"])
            and len(record["privacy"]["orders"]) > 1
            for record in all_records
        ),
        "finite_metrics": all(
            np.isfinite(value)
            for record in all_records
            for method in record["metrics"].values()
            for scope in method.values()
            for value in scope.values()
        ),
        "honest_provenance": all(
            record["baseline_label"] == "GAP-style inference-closed LP adaptation"
            and not record["official_reproduction"]
            for record in all_records
        ),
        "config_hash_current": all(
            record["external_config_sha256"]
            == sha256(ROOT / "configs" / "p3_external_baselines.json")
            for record in all_records
        ),
    }
    audit = {
        "protocol": "P3_2_GAP_STYLE_VALIDATION_AUDIT_v1",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "test_accessed": False,
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
