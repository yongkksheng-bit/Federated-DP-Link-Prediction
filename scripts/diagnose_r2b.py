"""Print a compact, descriptive diagnosis of the frozen R2B result."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path


RESULTS = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "r2b_end_to_end_synthetic"
    / "records.jsonl"
)


def describe(rows: list[dict]) -> None:
    print("regime,cert_n_mean,cert_n_min,cert_n_max,cert_gain_mean,cert_gain_max,"
          "eval_gain_mean,eval_gain_max,valid_bounds,max_lower_bound")
    for regime in sorted({row["regime"] for row in rows}):
        subset = [row for row in rows if row["regime"] == regime]
        counts = [row["certification_edges"] for row in subset]
        cert_gains = [row["certification_empirical_gain"] for row in subset]
        eval_gains = [row["evaluation_gain"] for row in subset]
        bounds = [
            row["certificate_lower_bound"]
            for row in subset
            if math.isfinite(row["certificate_lower_bound"])
        ]
        maximum_bound = max(bounds) if bounds else float("-inf")
        print(
            f"{regime},{statistics.mean(counts):.1f},{min(counts)},{max(counts)},"
            f"{statistics.mean(cert_gains):.6f},{max(cert_gains):.6f},"
            f"{statistics.mean(eval_gains):.6f},{max(eval_gains):.6f},"
            f"{len(bounds)},{maximum_bound:.6f}"
        )

    print("\nvisibility,valid_bounds,max_lower_bound,cert_gain_mean")
    for visibility in sorted({row["visibility"] for row in rows}):
        subset = [row for row in rows if row["visibility"] == visibility]
        bounds = [
            row["certificate_lower_bound"]
            for row in subset
            if math.isfinite(row["certificate_lower_bound"])
        ]
        maximum_bound = max(bounds) if bounds else float("-inf")
        print(
            f"{visibility},{len(bounds)},{maximum_bound:.6f},"
            f"{statistics.mean(row['certification_empirical_gain'] for row in subset):.6f}"
        )

    print("\ncert_epsilon,valid_bounds,max_lower_bound")
    for epsilon in sorted({row["cert_epsilon_target"] for row in rows}):
        subset = [row for row in rows if row["cert_epsilon_target"] == epsilon]
        bounds = [
            row["certificate_lower_bound"]
            for row in subset
            if math.isfinite(row["certificate_lower_bound"])
        ]
        maximum_bound = max(bounds) if bounds else float("-inf")
        print(f"{epsilon},{len(bounds)},{maximum_bound:.6f}")


if __name__ == "__main__":
    records = [
        json.loads(line)
        for line in RESULTS.read_text(encoding="utf-8").splitlines()
        if line
    ]
    describe(records)
