"""Run the frozen fresh Monte Carlo calibration of the R3 boundary."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy.stats import beta

from fed_dp_lp.accounting import calibrate_gaussian
from fed_dp_lp.certificate_boundary import (
    aggregate_noise_std,
    minimum_certification_count,
)
from fed_dp_lp.private_certificate import (
    block_rademacher_sums,
    certificate_lower_bound,
    one_sided_binomial_upper,
)
if __package__:
    from scripts.run_r3_feasibility_boundary import make_boundary
else:
    from run_r3_feasibility_boundary import make_boundary


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "r3_monte_carlo_calibration.json"
BOUNDARY_CONFIG_PATH = ROOT / "configs" / "r3_feasibility_boundary.json"
RESULTS = ROOT / "results" / "r3_monte_carlo_calibration"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def binomial_lower(successes: int, trials: int, confidence: float = 0.95) -> float:
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("invalid binomial inputs")
    if successes == 0:
        return 0.0
    return float(beta.ppf(1.0 - confidence, successes, trials - successes + 1))


def rounded_count(value: float, dependence: int) -> int:
    return max(dependence, math.ceil(value / dependence) * dependence)


def noisy_queries(
    rng: np.random.Generator,
    *,
    sums: np.ndarray,
    count: int,
    trials: int,
    client_noise_std: float,
    clients: int,
    visibility: str,
) -> tuple[np.ndarray, np.ndarray, float]:
    if visibility == "ideal_secagg":
        sum_noise = rng.normal(0.0, client_noise_std, size=trials)
        count_noise = rng.normal(0.0, client_noise_std, size=trials)
        return sums + sum_noise, count + count_noise, 0.0
    if visibility == "visible_messages":
        sum_messages = rng.normal(
            0.0, client_noise_std, size=(trials, clients)
        )
        count_messages = rng.normal(
            0.0, client_noise_std, size=(trials, clients)
        )
        sum_noise = sum_messages.sum(axis=1)
        count_noise = count_messages.sum(axis=1)
        aggregate_error = max(
            float(np.max(np.abs(sum_noise - sum_messages.sum(axis=1)))),
            float(np.max(np.abs(count_noise - count_messages.sum(axis=1)))),
        )
        return sums + sum_noise, count + count_noise, aggregate_error
    raise ValueError(f"unsupported visibility: {visibility}")


def run_cell(
    *,
    mean: float,
    count: int,
    epsilon: float,
    clients: int,
    visibility: str,
    dependence: int,
    trials: int,
    seed_sequence: list[int],
    boundary_config: dict,
    calibration,
    record_type: str,
    count_factor: float,
    predicted_count: int,
    commit: str,
) -> dict:
    rng = np.random.default_rng(np.random.SeedSequence(seed_sequence))
    sums = block_rademacher_sums(
        rng,
        trials=trials,
        count=count,
        dependence_factor=dependence,
        mean=mean,
    )
    noisy_sum, noisy_count, aggregate_error = noisy_queries(
        rng,
        sums=sums,
        count=count,
        trials=trials,
        client_noise_std=calibration.noise_std,
        clients=clients,
        visibility=visibility,
    )
    effective_noise = aggregate_noise_std(
        calibration.noise_std,
        clients=clients,
        visibility=visibility,
    )
    certificate = boundary_config["certificate"]
    allocation = certificate["failure_allocation"]
    result = certificate_lower_bound(
        noisy_sum,
        noisy_count,
        coordinate_noise_std=effective_noise,
        beta_sum=allocation["sum_noise"],
        beta_count=allocation["count_noise"],
        beta_sampling=allocation["sampling_validity"],
        dependence_factor=dependence,
        minimum_count_lower=certificate["minimum_noisy_count_lower"],
    )
    activated = result.lower_bound >= certificate["material_gain_gamma"]
    successes = int(activated.sum())
    return {
        "record_type": record_type,
        "protocol": "R3_CERTFED_LP_BOUNDARY_MONTE_CARLO_v1",
        "code_commit": commit,
        "config_sha256": sha256(CONFIG_PATH),
        "boundary_config_sha256": sha256(BOUNDARY_CONFIG_PATH),
        "real_data_accessed": False,
        "test_accessed": False,
        "population_effect": mean,
        "epsilon_target": epsilon,
        "epsilon_accounted": calibration.epsilon,
        "clients": clients,
        "visibility": visibility,
        "dependence_factor": dependence,
        "predicted_minimum_count": predicted_count,
        "count_factor": count_factor,
        "certification_count": count,
        "trials": trials,
        "activation_count": successes,
        "activation_rate": successes / trials,
        "activation_lower_95": binomial_lower(successes, trials),
        "activation_upper_95": one_sided_binomial_upper(successes, trials),
        "valid_certificate_rate": float(result.valid.mean()),
        "maximum_transcript_aggregate_error": aggregate_error,
    }


def generate_records(config: dict, boundary_config: dict, commit: str) -> list[dict]:
    records: list[dict] = []
    calibration_tolerance = boundary_config["accounting"]["calibration_tolerance"]
    calibrations = {
        epsilon: calibrate_gaussian(
            target_epsilon=epsilon,
            delta=boundary_config["delta"],
            sensitivity=boundary_config["certificate"]["l2_sensitivity"],
            tolerance=calibration_tolerance,
        )
        for epsilon in config["epsilon_grid"]
    }
    maximum_count = boundary_config["boundary_solver"][
        "maximum_certification_count"
    ]
    base_seed = config["rng_seed"]

    for epsilon_index, epsilon in enumerate(config["epsilon_grid"]):
        calibration = calibrations[epsilon]
        for visibility_index, visibility in enumerate(
            config["visibility_models"]
        ):
            effective_noise = aggregate_noise_std(
                calibration.noise_std,
                clients=config["clients"],
                visibility=visibility,
            )
            for dependence_index, dependence in enumerate(
                config["dependence_factors"]
            ):
                boundary = make_boundary(
                    boundary_config,
                    effective_noise=effective_noise,
                    dependence_factor=dependence,
                )
                predicted_by_effect = {
                    effect: minimum_certification_count(
                        effect, boundary, maximum_count=maximum_count
                    )
                    for effect in config["population_effects"]
                }
                for effect_index, effect in enumerate(
                    config["population_effects"]
                ):
                    predicted = predicted_by_effect[effect]
                    if predicted is None:
                        raise RuntimeError("registered effect has no finite boundary")
                    for factor_index, factor in enumerate(config["count_factors"]):
                        count = rounded_count(predicted * factor, dependence)
                        records.append(
                            run_cell(
                                mean=effect,
                                count=count,
                                epsilon=epsilon,
                                clients=config["clients"],
                                visibility=visibility,
                                dependence=dependence,
                                trials=config["trials_per_cell"],
                                seed_sequence=[
                                    base_seed,
                                    1,
                                    epsilon_index,
                                    visibility_index,
                                    dependence_index,
                                    effect_index,
                                    factor_index,
                                ],
                                boundary_config=boundary_config,
                                calibration=calibration,
                                record_type="power",
                                count_factor=factor,
                                predicted_count=predicted,
                                commit=commit,
                            )
                        )

                safety_predicted = minimum_certification_count(
                    config["safety_reference_effect"],
                    boundary,
                    maximum_count=maximum_count,
                )
                if safety_predicted is None:
                    raise RuntimeError("safety reference has no finite boundary")
                for effect_index, effect in enumerate(config["safety_effects"]):
                    for factor_index, factor in enumerate(
                        config["safety_count_factors"]
                    ):
                        count = rounded_count(
                            safety_predicted * factor, dependence
                        )
                        records.append(
                            run_cell(
                                mean=effect,
                                count=count,
                                epsilon=epsilon,
                                clients=config["clients"],
                                visibility=visibility,
                                dependence=dependence,
                                trials=config["trials_per_cell"],
                                seed_sequence=[
                                    base_seed,
                                    2,
                                    epsilon_index,
                                    visibility_index,
                                    dependence_index,
                                    effect_index,
                                    factor_index,
                                ],
                                boundary_config=boundary_config,
                                calibration=calibration,
                                record_type="safety",
                                count_factor=factor,
                                predicted_count=safety_predicted,
                                commit=commit,
                            )
                        )
    return records


def summarize(config: dict, records: list[dict]) -> dict:
    power = [row for row in records if row["record_type"] == "power"]
    safety = [row for row in records if row["record_type"] == "safety"]
    boundary_power = [
        row for row in power if math.isclose(row["count_factor"], 1.0)
    ]
    transition_ratios: list[float] = []
    transitions_observed = True
    group_keys = {
        (
            row["population_effect"],
            row["epsilon_target"],
            row["visibility"],
            row["dependence_factor"],
        )
        for row in power
    }
    for key in sorted(group_keys):
        subset = [
            row
            for row in power
            if (
                row["population_effect"],
                row["epsilon_target"],
                row["visibility"],
                row["dependence_factor"],
            )
            == key
        ]
        transitions = sorted(
            row["certification_count"]
            for row in subset
            if row["activation_rate"] >= 0.9
        )
        if not transitions:
            transitions_observed = False
            continue
        transition_ratios.append(
            subset[0]["predicted_minimum_count"] / transitions[0]
        )

    maximum_accountant_error = max(
        abs(row["epsilon_accounted"] - row["epsilon_target"])
        for row in records
    )
    metrics = {
        "record_count": len(records),
        "power_cells": len(power),
        "safety_cells": len(safety),
        "minimum_boundary_power": min(
            row["activation_rate"] for row in boundary_power
        ),
        "minimum_boundary_power_lower_95": min(
            row["activation_lower_95"] for row in boundary_power
        ),
        "maximum_safety_false_activation_rate": max(
            row["activation_rate"] for row in safety
        ),
        "maximum_safety_false_activation_upper_95": max(
            row["activation_upper_95"] for row in safety
        ),
        "maximum_predicted_to_empirical_transition_ratio": max(
            transition_ratios, default=math.inf
        ),
        "maximum_accountant_epsilon_error": maximum_accountant_error,
        "maximum_transcript_aggregate_error": max(
            row["maximum_transcript_aggregate_error"] for row in records
        ),
    }
    gate = config["registered_checks"]
    checks = {
        "boundary_power": metrics["minimum_boundary_power_lower_95"]
        >= gate["minimum_one_sided_95pct_power_lower_at_predicted_boundary"],
        "safety": metrics["maximum_safety_false_activation_upper_95"]
        <= gate["maximum_one_sided_95pct_false_activation_upper"],
        "transition_conservatism": metrics[
            "maximum_predicted_to_empirical_transition_ratio"
        ]
        <= gate["maximum_predicted_to_empirical_90pct_transition_ratio"],
        "all_transitions_observed": transitions_observed,
        "accountant_reproduction": maximum_accountant_error
        <= gate["accountant_reproduction_tolerance"],
        "all_metrics_finite": all(
            math.isfinite(value) for value in metrics.values()
        ),
        "real_data_access_prohibited": all(
            not row["real_data_accessed"] and not row["test_accessed"]
            for row in records
        ),
    }
    decision = (
        config["decision_if_checks_pass"]
        if all(checks.values())
        else config["decision_if_checks_fail"]
    )
    return {
        "protocol": config["protocol"],
        "metrics": metrics,
        "checks": checks,
        "decision": decision,
        "real_data_accessed": False,
        "test_accessed": False,
    }


def execute(write: bool = True) -> tuple[list[dict], dict]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    boundary_config = json.loads(
        BOUNDARY_CONFIG_PATH.read_text(encoding="utf-8")
    )
    records = generate_records(config, boundary_config, git_commit())
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
