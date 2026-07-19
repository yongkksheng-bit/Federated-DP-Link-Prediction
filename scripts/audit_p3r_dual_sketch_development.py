"""Audit completeness and privacy metadata of P3R dual-sketch development."""

import hashlib
import json
import pathlib

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER = json.loads((ROOT / "configs/p3_master_benchmark.json").read_text())
CONFIG_PATH = ROOT / "configs/p3r_dual_sketch_development.json"
CONFIG = json.loads(CONFIG_PATH.read_text())
OUTPUT = ROOT / "results/p3r_dual_sketch_development"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    grid = read_jsonl(OUTPUT / "grid_records.jsonl")
    held = read_jsonl(OUTPUT / "held_out_records.jsonl")
    summary = json.loads((OUTPUT / "summary.json").read_text())
    candidate = CONFIG["candidate"]
    decoder_count = (len(candidate["decoder_modes"])
                     * len(candidate["public_weights"])
                     * len(candidate["topology_weights"]))
    expected_grid = (len(MASTER["datasets"]) * len(MASTER["split"]["seeds"])
                     * len(candidate["dimension_pairs"])
                     * len(candidate["semantic_energy_fractions"])
                     * decoder_count)
    expected_held = len(MASTER["datasets"]) * len(MASTER["split"]["seeds"])
    checks = {
        "grid_complete": len(grid) == expected_grid,
        "held_out_complete": len(held) == expected_held,
        "summary_counts_match": summary["grid_record_count"] == expected_grid
        and summary["held_out_record_count"] == expected_held,
        "test_never_accessed": not summary["test_accessed"]
        and all(not record["test_accessed"] for record in held),
        "config_hash_current": all(
            record["p3r_config_sha256"] == sha256(CONFIG_PATH) for record in held
        ),
        "sensitivity_sqrt_two": all(
            np.isclose(record["l2_sensitivity"], np.sqrt(2.0)) for record in held
        ),
        "complete_rdp": all(
            len(record["privacy"]["orders"]) == len(record["privacy"]["rdp"])
            for record in held
        ),
        "joint_dimension_bounded": all(
            record["selected_config"]["joint_dimension"]
            <= candidate["maximum_joint_dimension"] for record in held
        ),
        "finite_metrics": all(np.isfinite(value) for record in held
            for method in record["metrics"].values()
            for scope in method.values() for value in scope.values()),
    }
    audit = {
        "protocol": "P3R_DUAL_SKETCH_DEVELOPMENT_AUDIT_v1",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "method_decision": summary["decision"],
        "test_accessed": False,
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
