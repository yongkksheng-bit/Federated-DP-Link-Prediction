"""Audit R5 output completeness, provenance, privacy, and decision logic."""

from __future__ import annotations

import json
import pathlib

import numpy as np

from fed_dp_lp.accounting import epsilon_from_rdp


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/r5_graph_phase_confirmatory.json"
OUTPUT = ROOT / "results/r5_graph_phase_confirmatory"


def read_jsonl(path: pathlib.Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    records = read_jsonl(OUTPUT / "records.jsonl")
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    access = json.loads((OUTPUT / "access.json").read_text(encoding="utf-8"))
    expected = (
        len(config["datasets"])
        * len(config["seeds"])
        * len(config["privacy"]["training_epsilon_grid"])
        * len(config["privacy"]["certification_epsilon_grid"])
        * len(config["privacy"]["visibility_models"])
    )
    primary = [record for record in records if record["confirmatory_primary"]]
    reproduced = []
    for record in records:
        privacy = record["composed_privacy"]
        epsilon, _ = epsilon_from_rdp(
            np.asarray(privacy["orders"]),
            np.asarray(privacy["rdp"]),
            delta=privacy["delta"],
        )
        reproduced.append(
            np.isclose(epsilon, privacy["epsilon"], rtol=0.0, atol=1e-12)
        )
    checks = {
        "record_grid_complete": len(records) == expected,
        "primary_exactly_30": (
            len(primary) == config["confirmatory_primary_cell"]["records"]
        ),
        "all_cells_unique": len(
            {
                (
                    row["dataset"],
                    row["seed"],
                    row["training_epsilon_target"],
                    row["certification_epsilon_target"],
                    row["visibility"],
                )
                for row in records
            }
        )
        == expected,
        "single_access": access["test_access_count"] == 1,
        "runner_commit_constant": len(
            {record["code_commit"] for record in records}
        )
        == 1,
        "no_test_tuning": all(record["test_tuning"] is False for record in records),
        "candidate_honestly_labeled": all(
            record["official_reproduction"] is False for record in records
        ),
        "accountants_reproduce": all(reproduced),
        "finite_values": all(
            np.isfinite(value)
            for record in records
            for value in (
                record["certification_empirical_advantage"],
                record["q5_pairwise_advantage"],
                record["full_holdout_pairwise_advantage"],
                record["q5_policy_pairwise_gain"],
                record["finite_population_penalty_audit_only"],
                record["composed_privacy"]["epsilon"],
            )
        ),
        "nonempty_disjoint_roles": all(
            record["certification_count"] > 0
            and record["evaluation_positive_count"] > 0
            for record in records
        ),
        "summary_record_count": (
            summary["provenance"]["record_count"] == expected
        ),
        "decision_label_valid": summary["decision"]
        in set(config["decision_labels"].values()),
    }
    audit = {
        "protocol": config["protocol"],
        "test_accessed": True,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "reported_decision": summary["decision"],
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit("R5 output audit failed")


if __name__ == "__main__":
    main()
