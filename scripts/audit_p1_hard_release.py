"""Post-hoc, machine-readable audit of the frozen hard DP control."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fed_dp_lp.metrics import paired_summary


INPUT = ROOT / "results" / "p1_pair_feature" / "records.jsonl"
OUTPUT = ROOT / "results" / "p1_pair_feature" / "hard_release_audit.json"
PUBLIC_METHODS = (
    "public_constant",
    "public_cosine",
    "public_negative_cosine",
    "public_same_hard",
    "public_different_hard",
)


def main() -> None:
    records = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines()]
    grouped = defaultdict(list)
    for record in records:
        if (
            record["visibility"] == "ideal_secagg"
            and record["epsilon_target"] in (2.0, 4.0)
            and record["feature_corruption"] in (0.25, 0.5)
        ):
            grouped[(
                record["domain"], record["epsilon_target"],
                record["feature_corruption"],
            )].append(record)

    comparisons = []
    for key, items in sorted(grouped.items()):
        domain, epsilon, corruption = key
        for metric in ("global", "cross"):
            hard = np.asarray([
                item["metrics"]["hard_group_dp"][metric] for item in items
            ])
            for public in PUBLIC_METHODS:
                baseline = np.asarray([
                    item["metrics"][public][metric] for item in items
                ])
                paired = paired_summary(hard, baseline)
                comparisons.append({
                    "domain": domain,
                    "epsilon": epsilon,
                    "feature_corruption": corruption,
                    "metric": metric,
                    "public_control": public,
                    "paired": paired,
                    "pass": paired["mean_difference"] >= 0.02
                    and paired["ci95_low"] > 0,
                })

    boundary = []
    for domain in sorted({record["domain"] for record in records}):
        items = [
            record for record in records
            if record["domain"] == domain
            and record["visibility"] == "ideal_secagg"
            and record["epsilon_target"] == 4.0
            and record["feature_corruption"] == 1.0
        ]
        hard = np.asarray([
            item["metrics"]["hard_group_dp"]["cross"] for item in items
        ])
        boundary.append({
            "domain": domain,
            "hard_cross_mean": float(np.mean(hard)),
            "comparisons": {
                public: paired_summary(
                    hard,
                    np.asarray([item["metrics"][public]["cross"] for item in items]),
                )
                for public in PUBLIC_METHODS
            },
        })

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    output = {
        "evidence_status": "post_hoc_exploratory_selection",
        "source_commit": commit,
        "input_protocol": "P1_PAIR_FEATURE_PROTOCOL_v1",
        "comparison_count": len(comparisons),
        "failed_comparisons": sum(not item["pass"] for item in comparisons),
        "decision": (
            "PROVISIONAL_P2_CANDIDATE"
            if all(item["pass"] for item in comparisons)
            else "DO_NOT_ADVANCE"
        ),
        "comparisons": comparisons,
        "high_corruption_boundary": boundary,
    }
    OUTPUT.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
