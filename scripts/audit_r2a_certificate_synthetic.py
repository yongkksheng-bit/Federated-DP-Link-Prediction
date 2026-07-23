"""Independently replay and audit the frozen R2A synthetic experiment."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np

from run_r2a_certificate_synthetic import generate_records, summarize


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/r2a_certificate_synthetic.json"
OUTPUT = ROOT / "results/r2a_certificate_synthetic"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    stored = [
        json.loads(line)
        for line in (OUTPUT / "records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    commits = {record["code_commit"] for record in stored}
    replayed = generate_records(config, code_commit=next(iter(commits)))
    replayed_summary = summarize(config, replayed)
    checks = {
        "record_count_complete": len(stored) == 1080 and len(replayed) == len(stored),
        "records_exactly_replayed": stored == replayed,
        "summary_exactly_replayed": summary == replayed_summary,
        "config_hash_current": all(
            record["config_sha256"] == sha256(CONFIG_PATH) for record in stored
        ),
        "single_frozen_code_commit": len(commits) == 1,
        "metrics_finite": all(
            np.isfinite(value) for value in summary["metrics"].values()
        ),
        "real_data_unaccessed": not summary["real_data_accessed"]
        and not summary["test_accessed"]
        and all(
            not record["real_data_accessed"] and not record["test_accessed"]
            for record in stored
        ),
    }
    audit = {
        "schema_version": 1,
        "protocol": config["protocol"] + "_AUDIT",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "decision_reproduced": replayed_summary["decision"],
        "real_data_accessed": False,
        "test_accessed": False,
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))
    if audit["status"] != "PASS":
        raise SystemExit("R2A audit failed")


if __name__ == "__main__":
    main()
