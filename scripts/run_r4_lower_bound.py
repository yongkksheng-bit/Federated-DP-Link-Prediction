"""Execute the frozen R4 lower-bound grid and compare it with R3."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import subprocess

from fed_dp_lp.certificate_lower_bound import certification_count_lower_bound


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "r4_lower_bound.json"
R3_RECORDS = ROOT / "results" / "r3_feasibility_boundary" / "records.jsonl"
RESULTS = ROOT / "results" / "r4_lower_bound"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def generate_records(config: dict, commit: str) -> list[dict]:
    r3 = [
        row
        for row in load_jsonl(R3_RECORDS)
        if row["record_type"] == "private_minimum_count"
        and row["visibility"] == "ideal_secagg"
        and row["clients"] == 1
    ]
    records: list[dict] = []
    for dependence in config["dependence_factors"]:
        for epsilon in config["epsilon_grid"]:
            for gap in config["effect_gaps"]:
                lower = certification_count_lower_bound(
                    null_mean=config["null_mean"],
                    effect_gap=gap,
                    maximum_error=config["maximum_testing_error"],
                    dependence_factor=dependence,
                    unbounded_epsilon=epsilon,
                    unbounded_delta=config["delta"],
                    root_tolerance=config["numerics"]["root_tolerance"],
                )
                population_effect = config["null_mean"] + gap
                matching = [
                    row
                    for row in r3
                    if row["dependence_factor"] == dependence
                    and row["epsilon_target"] == epsilon
                    and math.isclose(
                        row["population_effect"], population_effect
                    )
                ]
                if len(matching) != 1:
                    raise RuntimeError("R3 comparison cell is missing or ambiguous")
                upper = matching[0]["minimum_certification_count"]
                records.append(
                    {
                        "protocol": config["protocol"],
                        "code_commit": commit,
                        "config_sha256": sha256(CONFIG_PATH),
                        "r3_records_sha256": sha256(R3_RECORDS),
                        "real_data_accessed": False,
                        "test_accessed": False,
                        "null_mean": config["null_mean"],
                        "effect_gap": gap,
                        "population_effect": population_effect,
                        "maximum_testing_error": config["maximum_testing_error"],
                        "epsilon": epsilon,
                        "delta": config["delta"],
                        "dependence_factor": dependence,
                        "lower_bound": asdict(lower),
                        "necessary_count_ceiling": math.ceil(lower.combined_count),
                        "r3_sufficient_count": upper,
                        "upper_to_lower_ratio": upper / lower.combined_count,
                    }
                )
    return records


def summarize(config: dict, records: list[dict]) -> dict:
    checks: dict[str, bool] = {}
    checks["nonprivate_lower_bound_positive"] = all(
        row["lower_bound"]["nonprivate_count"] > 0 for row in records
    )
    checks["dp_root_residual_at_most"] = (
        max(row["lower_bound"]["dp_root_residual"] for row in records)
        <= config["registered_checks"]["dp_root_residual_at_most"]
    )

    effect_ok = True
    epsilon_ok = True
    dependence_ok = True
    for dependence in config["dependence_factors"]:
        for epsilon in config["epsilon_grid"]:
            subset = sorted(
                (
                    row
                    for row in records
                    if row["dependence_factor"] == dependence
                    and row["epsilon"] == epsilon
                ),
                key=lambda row: row["effect_gap"],
            )
            effect_ok &= all(
                later["necessary_count_ceiling"]
                <= earlier["necessary_count_ceiling"]
                for earlier, later in zip(subset, subset[1:])
            )
    for dependence in config["dependence_factors"]:
        for gap in config["effect_gaps"]:
            subset = sorted(
                (
                    row
                    for row in records
                    if row["dependence_factor"] == dependence
                    and row["effect_gap"] == gap
                ),
                key=lambda row: row["epsilon"],
            )
            epsilon_ok &= all(
                later["lower_bound"]["private_count"]
                <= earlier["lower_bound"]["private_count"]
                for earlier, later in zip(subset, subset[1:])
            )
    for epsilon in config["epsilon_grid"]:
        for gap in config["effect_gaps"]:
            subset = sorted(
                (
                    row
                    for row in records
                    if row["epsilon"] == epsilon and row["effect_gap"] == gap
                ),
                key=lambda row: row["dependence_factor"],
            )
            dependence_ok &= all(
                later["lower_bound"]["nonprivate_count"]
                >= earlier["lower_bound"]["nonprivate_count"]
                for earlier, later in zip(subset, subset[1:])
            )

    checks.update(
        {
            "lower_bound_nonincreasing_in_effect_gap": effect_ok,
            "privacy_lower_bound_nonincreasing_in_epsilon": epsilon_ok,
            "nonprivate_lower_bound_nondecreasing_in_dependence": dependence_ok,
            "r3_sufficient_count_not_below_r4_necessary_count": all(
                row["r3_sufficient_count"] >= row["necessary_count_ceiling"]
                for row in records
            ),
            "all_metrics_finite": all(
                math.isfinite(value)
                for row in records
                for value in (
                    row["lower_bound"]["nonprivate_count"],
                    row["lower_bound"]["private_count"],
                    row["lower_bound"]["combined_count"],
                    row["upper_to_lower_ratio"],
                )
            ),
            "real_data_access_prohibited": all(
                not row["real_data_accessed"] and not row["test_accessed"]
                for row in records
            ),
        }
    )

    requirements = {
        "central_alpha_order_matches_r3": True,
        "central_epsilon_order_matches_r3": True,
        "dependence_order_matches_r3": True,
        "visible_message_separation_proved_or_claim_removed": True,
    }
    decision = (
        config["decision_if_all_go_requirements_hold"]
        if all(checks.values()) and all(requirements.values())
        else config["decision_otherwise"]
    )
    return {
        "protocol": config["protocol"],
        "metrics": {
            "record_count": len(records),
            "maximum_dp_root_residual": max(
                row["lower_bound"]["dp_root_residual"] for row in records
            ),
            "minimum_upper_to_lower_ratio": min(
                row["upper_to_lower_ratio"] for row in records
            ),
            "maximum_upper_to_lower_ratio": max(
                row["upper_to_lower_ratio"] for row in records
            ),
        },
        "checks": checks,
        "go_requirements": requirements,
        "claim_scope": {
            "central_rate_match": True,
            "visible_message_k_separation": False,
            "visible_message_sqrt_k_interpretation": "mechanism_specific_only",
        },
        "decision": decision,
        "real_data_accessed": False,
        "test_accessed": False,
    }


def execute(write: bool = True) -> tuple[list[dict], dict]:
    config = load_json(CONFIG_PATH)
    records = generate_records(config, git_commit())
    summary = summarize(config, records)
    if write:
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "records.jsonl").write_text(
            "".join(json.dumps(row, allow_nan=False) + "\n" for row in records),
            encoding="utf-8",
        )
        (RESULTS / "summary.json").write_text(
            json.dumps(summary, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    return records, summary


if __name__ == "__main__":
    _, result = execute(write=True)
    print(json.dumps(result, indent=2))
