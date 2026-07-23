"""Run the frozen R2A synthetic private-certificate experiment."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.private_certificate import (
    CERTIFICATION_L2_SENSITIVITY,
    block_rademacher_sums,
    certificate_lower_bound,
    one_sided_binomial_upper,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/r2a_certificate_synthetic.json"
OUTPUT = ROOT / "results/r2a_certificate_synthetic"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def cell_seed(base: int, indices: tuple[int, ...]) -> np.random.SeedSequence:
    return np.random.SeedSequence([base, *indices])


def generate_records(config: dict, *, code_commit: str) -> list[dict]:
    certificate = config["certificate"]
    allocation = certificate["failure_allocation"]
    records: list[dict] = []
    for mean_index, true_mean in enumerate(config["true_means"]):
        for count_index, count in enumerate(config["certification_counts"]):
            for epsilon_index, epsilon in enumerate(config["epsilon_grid"]):
                calibration = calibrate_gaussian(
                    target_epsilon=epsilon,
                    delta=config["delta"],
                    sensitivity=CERTIFICATION_L2_SENSITIVITY,
                    steps=certificate["gaussian_releases"],
                    orders=DEFAULT_ORDERS,
                    tolerance=1e-13,
                )
                for client_index, clients in enumerate(config["clients"]):
                    for visibility_index, visibility in enumerate(
                        config["visibility_models"]
                    ):
                        for dependence_index, dependence in enumerate(
                            config["dependence_factors"]
                        ):
                            rng = np.random.default_rng(
                                cell_seed(
                                    config["rng_seed"],
                                    (
                                        mean_index,
                                        count_index,
                                        epsilon_index,
                                        client_index,
                                        visibility_index,
                                        dependence_index,
                                    ),
                                )
                            )
                            trials = config["trials_per_cell"]
                            exact_sum = block_rademacher_sums(
                                rng,
                                trials=trials,
                                count=count,
                                dependence_factor=dependence,
                                mean=true_mean,
                            )
                            multiplier = (
                                np.sqrt(clients)
                                if visibility == "visible_messages"
                                else 1.0
                            )
                            aggregate_std = calibration.noise_std * multiplier
                            noisy_sum = exact_sum + rng.normal(
                                0.0, aggregate_std, size=trials
                            )
                            noisy_count = count + rng.normal(
                                0.0, aggregate_std, size=trials
                            )
                            certificate_result = certificate_lower_bound(
                                noisy_sum,
                                noisy_count,
                                coordinate_noise_std=aggregate_std,
                                beta_sum=allocation["sum_noise"],
                                beta_count=allocation["count_noise"],
                                beta_sampling=allocation["sampling"],
                                dependence_factor=dependence,
                                minimum_count_lower=certificate[
                                    "minimum_noisy_count_lower"
                                ],
                            )
                            lower = certificate_result.lower_bound
                            activated = lower >= certificate["material_gain_gamma"]
                            safety_violations = int(np.sum(lower > true_mean))
                            false_activations = int(
                                np.sum(activated)
                                if true_mean < certificate["material_gain_gamma"]
                                else 0
                            )
                            activations = int(np.sum(activated))
                            records.append(
                                {
                                    "protocol": config["protocol"],
                                    "code_commit": code_commit,
                                    "config_sha256": sha256(CONFIG_PATH),
                                    "real_data_accessed": False,
                                    "test_accessed": False,
                                    "true_mean": true_mean,
                                    "count": count,
                                    "epsilon_target": epsilon,
                                    "clients": clients,
                                    "visibility": visibility,
                                    "dependence_factor": dependence,
                                    "trials": trials,
                                    "privacy": asdict(calibration),
                                    "aggregate_coordinate_noise_std": float(
                                        aggregate_std
                                    ),
                                    "sum_noise_bound": certificate_result.sum_noise_bound,
                                    "count_noise_bound": certificate_result.count_noise_bound,
                                    "valid_certificates": int(
                                        certificate_result.valid.sum()
                                    ),
                                    "activations": activations,
                                    "activation_rate": activations / trials,
                                    "safety_violations": safety_violations,
                                    "safety_violation_rate": safety_violations
                                    / trials,
                                    "safety_violation_upper_95": one_sided_binomial_upper(
                                        safety_violations, trials
                                    ),
                                    "false_activations": false_activations,
                                    "false_activation_rate": false_activations
                                    / trials,
                                    "false_activation_upper_95": one_sided_binomial_upper(
                                        false_activations, trials
                                    ),
                                }
                            )
    return records


def summarize(config: dict, records: list[dict]) -> dict:
    gate = config["go_no_go_gate"]
    gamma = config["certificate"]["material_gain_gamma"]
    safety = [record for record in records if record["true_mean"] < gamma]
    positive = [record for record in records if record["true_mean"] > gamma]
    registered = config["registered_power_cells"]
    ideal_power = [
        record["activation_rate"]
        for record in records
        if record["true_mean"] >= registered["true_mean_minimum"]
        and record["count"] >= registered["certification_count_minimum"]
        and record["epsilon_target"] >= registered["epsilon_minimum"]
        and record["dependence_factor"] == registered["dependence_factor"]
        and record["visibility"] == "ideal_secagg"
    ]
    visible_power = [
        record["activation_rate"]
        for record in records
        if record["true_mean"] >= registered["true_mean_minimum"]
        and record["count"] >= registered["certification_count_minimum"]
        and record["epsilon_target"] >= registered["epsilon_minimum"]
        and record["dependence_factor"] == registered["dependence_factor"]
        and record["visibility"] == "visible_messages"
        and record["clients"] <= registered["visible_messages_max_clients"]
    ]
    epsilon_errors = [
        abs(record["privacy"]["epsilon"] - record["epsilon_target"])
        for record in records
    ]
    metrics = {
        "record_count": len(records),
        "trial_count": int(sum(record["trials"] for record in records)),
        "maximum_safety_violation_rate": max(
            record["safety_violation_rate"] for record in safety
        ),
        "maximum_safety_violation_upper_95": max(
            record["safety_violation_upper_95"] for record in safety
        ),
        "maximum_false_activation_rate_below_gamma": max(
            record["false_activation_rate"] for record in safety
        ),
        "maximum_false_activation_upper_95": max(
            record["false_activation_upper_95"] for record in safety
        ),
        "minimum_registered_ideal_power": min(ideal_power),
        "minimum_registered_visible_power": min(visible_power),
        "positive_cell_activation_fraction": float(
            sum(record["activations"] for record in positive)
            / sum(record["trials"] for record in positive)
        ),
        "maximum_accountant_epsilon_error": max(epsilon_errors),
    }
    checks = {
        "safety_violation_rate": metrics["maximum_safety_violation_rate"]
        <= gate["maximum_safety_violation_rate"],
        "false_activation_rate": metrics[
            "maximum_false_activation_rate_below_gamma"
        ]
        <= gate["maximum_false_activation_rate_below_gamma"],
        "safety_binomial_upper": metrics["maximum_safety_violation_upper_95"]
        <= gate["require_each_rate_one_sided_95pct_binomial_upper_at_most"],
        "false_activation_binomial_upper": metrics[
            "maximum_false_activation_upper_95"
        ]
        <= gate["require_each_rate_one_sided_95pct_binomial_upper_at_most"],
        "ideal_power": metrics["minimum_registered_ideal_power"]
        >= gate["minimum_registered_ideal_power"],
        "visible_power": metrics["minimum_registered_visible_power"]
        >= gate["minimum_registered_visible_power"],
        "positive_nontriviality": metrics["positive_cell_activation_fraction"]
        >= gate["minimum_positive_cell_activation_fraction"],
        "accountant_reproduced": metrics["maximum_accountant_epsilon_error"]
        <= gate["accountant_reproduction_tolerance"],
        "all_metrics_finite": all(np.isfinite(value) for value in metrics.values()),
        "real_data_unaccessed": all(
            not record["real_data_accessed"] and not record["test_accessed"]
            for record in records
        ),
    }
    return {
        "protocol": config["protocol"],
        "metrics": metrics,
        "checks": checks,
        "decision": config["decision_if_pass"]
        if all(checks.values())
        else config["decision_if_fail"],
        "real_data_accessed": False,
        "test_accessed": False,
    }


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("R2A output exists; refusing overwrite")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    records = generate_records(config, code_commit=git_head())
    summary = summarize(config, records)
    OUTPUT.mkdir(parents=True)
    with (OUTPUT / "records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
