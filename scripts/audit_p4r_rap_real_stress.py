"""Audit fixed RAP real-graph stress artifacts."""

import hashlib
import json
import pathlib

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p4r_rap_real_stress.json"
MASTER = json.loads((ROOT / "configs/p3_master_benchmark.json").read_text())
OUTPUT = ROOT / "results/p4r_rap_real_stress"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    records = [json.loads(line) for line in (OUTPUT / "records.jsonl").read_text().splitlines()]
    summary = json.loads((OUTPUT / "summary.json").read_text())
    expected = len(MASTER["datasets"]) * len(MASTER["split"]["seeds"])
    checks = {
        "records_complete": len(records) == expected == summary["record_count"],
        "test_never_accessed": not summary["test_accessed"]
        and all(not r["test_accessed"] for r in records),
        "config_hash_current": all(r["config_sha256"] == sha256(CONFIG_PATH) for r in records),
        "sensitivity_sqrt_two": all(np.isclose(r["l2_sensitivity_per_release"], np.sqrt(2.0)) for r in records),
        "complete_rdp": all(len(r["privacy"]["orders"]) == len(r["privacy"]["rdp"])
                            and r["privacy"]["steps"] == r["release_count"] for r in records),
        "fixed_rap_config": all(
            r["selected_config"]["profile_energy_fraction"] == 0.5
            and r["selected_config"]["profile_weight"] == 2.0
            and r["selected_config"]["prior_strength"] == 1.0 for r in records
        ),
        "finite_metrics": all(np.isfinite(value) for r in records
            for method in r["metrics"].values() for scope in method.values()
            for value in scope.values()),
    }
    audit = {
        "protocol": "P4R_RAP_FIXED_REAL_STRESS_v1_AUDIT",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "method_decision": summary["decision"],
        "test_accessed": False,
    }
    (OUTPUT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
