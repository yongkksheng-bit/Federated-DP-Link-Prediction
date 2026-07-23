"""Exactly replay the frozen R3 Monte Carlo calibration."""

from __future__ import annotations

import json

from run_r3_monte_carlo_calibration import RESULTS, execute


def main() -> None:
    stored_records = [
        json.loads(line)
        for line in (RESULTS / "records.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    stored_summary = json.loads(
        (RESULTS / "summary.json").read_text(encoding="utf-8")
    )
    replay_records, replay_summary = execute(write=False)
    audit = {
        "schema_version": 1,
        "protocol": "R3_CERTFED_LP_BOUNDARY_MONTE_CARLO_v1_AUDIT",
        "status": "PASS"
        if stored_records == replay_records and stored_summary == replay_summary
        else "FAIL",
        "checks": {
            "records_exactly_replayed": stored_records == replay_records,
            "summary_exactly_replayed": stored_summary == replay_summary,
            "real_data_unaccessed": not any(
                row["real_data_accessed"] or row["test_accessed"]
                for row in replay_records
            ),
        },
        "decision_reproduced": replay_summary["decision"],
        "real_data_accessed": False,
        "test_accessed": False,
    }
    (RESULTS / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
