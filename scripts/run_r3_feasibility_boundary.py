"""Execute the frozen R3 analytical feasibility-boundary grid."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import subprocess

from fed_dp_lp.accounting import calibrate_gaussian
from fed_dp_lp.certificate_boundary import (
    CertificateBoundary,
    activation_power_lower_bound,
    aggregate_noise_std,
    minimum_certification_count,
    minimum_detectable_effect,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "r3_feasibility_boundary.json"
RESULTS = ROOT / "results" / "r3_feasibility_boundary"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def make_boundary(
    config: dict,
    *,
    effective_noise: float,
    dependence_factor: float,
) -> CertificateBoundary:
    certificate = config["certificate"]
    allocation = certificate["failure_allocation"]
    return CertificateBoundary(
        gamma=certificate["material_gain_gamma"],
        beta_sum=allocation["sum_noise"],
        beta_count=allocation["count_noise"],
        beta_sampling=allocation["sampling_validity"],
        beta_power=allocation["power_sampling"],
        dependence_factor=dependence_factor,
        minimum_count_lower=certificate["minimum_noisy_count_lower"],
        effective_noise_std=effective_noise,
    )


def generate_records(config: dict, commit: str) -> list[dict]:
    records: list[dict] = []
    maximum_count = config["boundary_solver"]["maximum_certification_count"]
    tolerance = config["accounting"]["calibration_tolerance"]

    calibrations = {
        epsilon: calibrate_gaussian(
            target_epsilon=epsilon,
            delta=config["delta"],
            sensitivity=config["certificate"]["l2_sensitivity"],
            tolerance=tolerance,
        )
        for epsilon in config["epsilon_grid"]
    }

    for epsilon, calibration in calibrations.items():
        for clients in config["clients"]:
            for visibility in config["visibility_models"]:
                effective_noise = aggregate_noise_std(
                    calibration.noise_std,
                    clients=clients,
                    visibility=visibility,
                )
                for dependence in config["dependence_factors"]:
                    boundary = make_boundary(
                        config,
                        effective_noise=effective_noise,
                        dependence_factor=dependence,
                    )
                    for effect in config["population_effect_grid"]:
                        count = minimum_certification_count(
                            effect,
                            boundary,
                            maximum_count=maximum_count,
                        )
                        records.append(
                            {
                                "record_type": "private_minimum_count",
                                "protocol": config["protocol"],
                                "code_commit": commit,
                                "config_sha256": sha256(CONFIG_PATH),
                                "real_data_accessed": False,
                                "test_accessed": False,
                                "epsilon_target": epsilon,
                                "epsilon_accounted": calibration.epsilon,
                                "delta": config["delta"],
                                "client_noise_std": calibration.noise_std,
                                "effective_noise_std": effective_noise,
                                "clients": clients,
                                "visibility": visibility,
                                "dependence_factor": dependence,
                                "population_effect": effect,
                                "minimum_certification_count": count,
                                "boundary": asdict(boundary),
                            }
                        )
                    for count in config["boundary_solver"]["inverse_effect_counts"]:
                        records.append(
                            {
                                "record_type": "private_minimum_effect",
                                "protocol": config["protocol"],
                                "code_commit": commit,
                                "config_sha256": sha256(CONFIG_PATH),
                                "real_data_accessed": False,
                                "test_accessed": False,
                                "epsilon_target": epsilon,
                                "epsilon_accounted": calibration.epsilon,
                                "delta": config["delta"],
                                "client_noise_std": calibration.noise_std,
                                "effective_noise_std": effective_noise,
                                "clients": clients,
                                "visibility": visibility,
                                "dependence_factor": dependence,
                                "certification_count": count,
                                "minimum_detectable_effect": minimum_detectable_effect(
                                    count, boundary
                                ),
                                "boundary": asdict(boundary),
                            }
                        )

    for dependence in config["dependence_factors"]:
        boundary = make_boundary(
            config,
            effective_noise=0.0,
            dependence_factor=dependence,
        )
        for effect in config["population_effect_grid"]:
            records.append(
                {
                    "record_type": "nonprivate_minimum_count",
                    "protocol": config["protocol"],
                    "code_commit": commit,
                    "config_sha256": sha256(CONFIG_PATH),
                    "real_data_accessed": False,
                    "test_accessed": False,
                    "dependence_factor": dependence,
                    "population_effect": effect,
                    "minimum_certification_count": minimum_certification_count(
                        effect, boundary, maximum_count=maximum_count
                    ),
                    "boundary": asdict(boundary),
                }
            )
        for count in config["boundary_solver"]["inverse_effect_counts"]:
            records.append(
                {
                    "record_type": "nonprivate_minimum_effect",
                    "protocol": config["protocol"],
                    "code_commit": commit,
                    "config_sha256": sha256(CONFIG_PATH),
                    "real_data_accessed": False,
                    "test_accessed": False,
                    "dependence_factor": dependence,
                    "certification_count": count,
                    "minimum_detectable_effect": minimum_detectable_effect(
                        count, boundary
                    ),
                    "boundary": asdict(boundary),
                }
            )
    return records


def summarize(config: dict, records: list[dict]) -> dict:
    private_counts = [
        row for row in records if row["record_type"] == "private_minimum_count"
    ]
    checks: dict[str, bool] = {}

    checks["all_registered_boundaries_finite"] = all(
        row["minimum_certification_count"] is not None for row in private_counts
    )
    checks["integer_boundary_exact_against_local_bruteforce"] = all(
        activation_power_lower_bound(
            row["minimum_certification_count"],
            row["population_effect"],
            CertificateBoundary(**row["boundary"]),
        )
        >= row["boundary"]["gamma"]
        and activation_power_lower_bound(
            row["minimum_certification_count"] - 1,
            row["population_effect"],
            CertificateBoundary(**row["boundary"]),
        )
        < row["boundary"]["gamma"]
        for row in private_counts
        if row["minimum_certification_count"] is not None
    )

    def count_map(**fixed: object) -> dict[object, int]:
        subset = [
            row
            for row in private_counts
            if all(row[key] == value for key, value in fixed.items())
        ]
        return {
            (
                row["population_effect"],
                row["epsilon_target"],
                row["clients"],
                row["visibility"],
                row["dependence_factor"],
            ): row["minimum_certification_count"]
            for row in subset
        }

    effect_ok = True
    epsilon_ok = True
    dependence_ok = True
    ideal_ok = True
    visible_ok = True
    for visibility in config["visibility_models"]:
        for clients in config["clients"]:
            for dependence in config["dependence_factors"]:
                for epsilon in config["epsilon_grid"]:
                    values = [
                        count_map(
                            visibility=visibility,
                            clients=clients,
                            dependence_factor=dependence,
                            epsilon_target=epsilon,
                        )[
                            (effect, epsilon, clients, visibility, dependence)
                        ]
                        for effect in config["population_effect_grid"]
                    ]
                    effect_ok &= all(
                        later <= earlier
                        for earlier, later in zip(values, values[1:])
                    )
        for clients in config["clients"]:
            for dependence in config["dependence_factors"]:
                for effect in config["population_effect_grid"]:
                    values = [
                        count_map(
                            visibility=visibility,
                            clients=clients,
                            dependence_factor=dependence,
                            population_effect=effect,
                        )[
                            (effect, epsilon, clients, visibility, dependence)
                        ]
                        for epsilon in config["epsilon_grid"]
                    ]
                    epsilon_ok &= all(
                        later <= earlier
                        for earlier, later in zip(values, values[1:])
                    )

    for epsilon in config["epsilon_grid"]:
        for clients in config["clients"]:
            for visibility in config["visibility_models"]:
                for effect in config["population_effect_grid"]:
                    values = [
                        count_map(
                            epsilon_target=epsilon,
                            clients=clients,
                            visibility=visibility,
                            population_effect=effect,
                        )[
                            (effect, epsilon, clients, visibility, dependence)
                        ]
                        for dependence in config["dependence_factors"]
                    ]
                    dependence_ok &= all(
                        later >= earlier
                        for earlier, later in zip(values, values[1:])
                    )

    for epsilon in config["epsilon_grid"]:
        for dependence in config["dependence_factors"]:
            for effect in config["population_effect_grid"]:
                ideal_values = [
                    count_map(
                        epsilon_target=epsilon,
                        visibility="ideal_secagg",
                        dependence_factor=dependence,
                        population_effect=effect,
                    )[(effect, epsilon, clients, "ideal_secagg", dependence)]
                    for clients in config["clients"]
                ]
                ideal_ok &= len(set(ideal_values)) == 1
                visible_values = [
                    count_map(
                        epsilon_target=epsilon,
                        visibility="visible_messages",
                        dependence_factor=dependence,
                        population_effect=effect,
                    )[(effect, epsilon, clients, "visible_messages", dependence)]
                    for clients in config["clients"]
                ]
                visible_ok &= all(
                    later >= earlier
                    for earlier, later in zip(visible_values, visible_values[1:])
                )

    inverse_ok = True
    for row in private_counts:
        count = row["minimum_certification_count"]
        if count is None:
            inverse_ok = False
            continue
        boundary = CertificateBoundary(**row["boundary"])
        inverse_ok &= (
            minimum_detectable_effect(count, boundary)
            <= row["population_effect"] + 1e-12
        )
        if count > 1:
            inverse_ok &= (
                minimum_detectable_effect(count - 1, boundary)
                > row["population_effect"] - 1e-12
            )

    checks.update(
        {
            "minimum_count_nonincreasing_in_population_effect": effect_ok,
            "minimum_count_nonincreasing_in_epsilon": epsilon_ok,
            "minimum_count_nondecreasing_in_dependence_factor": dependence_ok,
            "ideal_secagg_invariant_to_client_count": ideal_ok,
            "visible_messages_nondecreasing_in_client_count": visible_ok,
            "forward_inverse_boundary_consistency": inverse_ok,
            "accountant_reproduction_tolerance": max(
                abs(row["epsilon_accounted"] - row["epsilon_target"])
                for row in private_counts
            )
            <= config["registered_checks"]["accountant_reproduction_tolerance"],
            "real_data_access_prohibited": all(
                not row["real_data_accessed"] and not row["test_accessed"]
                for row in records
            ),
            "all_values_finite": all(
                math.isfinite(value)
                for row in records
                for key, value in row.items()
                if key
                in {
                    "epsilon_accounted",
                    "client_noise_std",
                    "effective_noise_std",
                    "minimum_detectable_effect",
                }
            ),
        }
    )
    decision = (
        config["decision_if_checks_pass"]
        if all(checks.values())
        else config["decision_if_checks_fail"]
    )
    return {
        "protocol": config["protocol"],
        "record_count": len(records),
        "private_minimum_count_records": len(private_counts),
        "checks": checks,
        "decision": decision,
        "real_data_accessed": False,
        "test_accessed": False,
    }


def execute(write: bool = True) -> tuple[list[dict], dict]:
    config = load_config()
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
