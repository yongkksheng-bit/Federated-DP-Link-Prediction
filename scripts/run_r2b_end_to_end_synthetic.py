"""Run frozen end-to-end CertFed-LP synthetic graphs."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.certfed_synthetic import (
    corrupted_pairs,
    generate_sbm_graph,
    pairwise_advantages,
    partition_edges,
    release_certification_query,
    release_training_channels,
)
from fed_dp_lp.conservative_selector import mean_t_interval
from fed_dp_lp.private_certificate import (
    CERTIFICATION_L2_SENSITIVITY,
    certificate_lower_bound,
    one_sided_binomial_upper,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/r2b_end_to_end_synthetic.json"
OUTPUT = ROOT / "results/r2b_end_to_end_synthetic"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def generate_records(config: dict, *, code_commit: str) -> list[dict]:
    graph_config = config["graph"]
    partition = config["edge_partition"]
    training_config = config["training_branch"]
    certification = config["certification"]
    train_calibrations = {
        epsilon: calibrate_gaussian(
            target_epsilon=epsilon,
            delta=training_config["delta"],
            sensitivity=CERTIFICATION_L2_SENSITIVITY,
            steps=training_config["hops"],
            orders=DEFAULT_ORDERS,
            tolerance=1e-13,
        )
        for epsilon in training_config["epsilon_grid"]
    }
    cert_calibrations = {
        epsilon: calibrate_gaussian(
            target_epsilon=epsilon,
            delta=certification["delta"],
            sensitivity=CERTIFICATION_L2_SENSITIVITY,
            steps=1,
            orders=DEFAULT_ORDERS,
            tolerance=1e-13,
        )
        for epsilon in certification["epsilon_grid"]
    }
    allocation = certification["failure_allocation"]
    records: list[dict] = []
    for regime_index, (regime, parameters) in enumerate(
        graph_config["regimes"].items()
    ):
        for seed in range(graph_config["seeds"]):
            graph_seed = graph_config["base_seed"] + regime_index * 1000 + seed
            graph = generate_sbm_graph(
                nodes=graph_config["nodes"],
                communities=graph_config["communities"],
                clients=graph_config["clients"],
                p_in=parameters["p_in"],
                p_out=parameters["p_out"],
                feature_noise=parameters["public_feature_noise"],
                seed=graph_seed,
            )
            train_edges, cert_edges, eval_edges = partition_edges(
                graph.edges,
                nodes=graph_config["nodes"],
                seed=graph_seed + 100000,
                training_fraction=partition["training_fraction"],
                certification_fraction=partition["certification_fraction"],
            )
            if min(len(train_edges), len(cert_edges), len(eval_edges)) == 0:
                raise RuntimeError(f"empty split for {regime} seed {seed}")
            cert_comparisons = corrupted_pairs(
                cert_edges, nodes=graph_config["nodes"], seed=graph_seed + 200000
            )
            eval_comparisons = corrupted_pairs(
                eval_edges, nodes=graph_config["nodes"], seed=graph_seed + 300000
            )
            public_channels = (graph.features,)
            for train_epsilon_index, train_epsilon in enumerate(
                training_config["epsilon_grid"]
            ):
                train_calibration = train_calibrations[train_epsilon]
                for visibility_index, visibility in enumerate(
                    certification["visibility_models"]
                ):
                    training_rng = np.random.default_rng(
                        np.random.SeedSequence(
                            [
                                graph_config["base_seed"],
                                regime_index,
                                seed,
                                train_epsilon_index,
                                visibility_index,
                                7001,
                            ]
                        )
                    )
                    training_release = release_training_channels(
                        train_edges,
                        graph.features,
                        graph.homes,
                        clients=graph_config["clients"],
                        noise_std=train_calibration.noise_std,
                        visibility=visibility,
                        rng=training_rng,
                    )
                    cert_advantages = pairwise_advantages(
                        public_channels,
                        training_release.channels,
                        cert_edges,
                        cert_comparisons,
                    )
                    eval_advantages = pairwise_advantages(
                        public_channels,
                        training_release.channels,
                        eval_edges,
                        eval_comparisons,
                    )
                    owners = graph.homes[cert_edges[:, 0]]
                    evaluation_gain = float(eval_advantages.mean())
                    for cert_epsilon_index, cert_epsilon in enumerate(
                        certification["epsilon_grid"]
                    ):
                        cert_calibration = cert_calibrations[cert_epsilon]
                        cert_rng = np.random.default_rng(
                            np.random.SeedSequence(
                                [
                                    graph_config["base_seed"],
                                    regime_index,
                                    seed,
                                    train_epsilon_index,
                                    cert_epsilon_index,
                                    visibility_index,
                                    9001,
                                ]
                            )
                        )
                        cert_release = release_certification_query(
                            cert_advantages,
                            owners,
                            clients=graph_config["clients"],
                            noise_std=cert_calibration.noise_std,
                            visibility=visibility,
                            rng=cert_rng,
                        )
                        aggregate_std = cert_calibration.noise_std * (
                            np.sqrt(graph_config["clients"])
                            if visibility == "visible_messages"
                            else 1.0
                        )
                        bound = certificate_lower_bound(
                            np.asarray([cert_release.noisy_sum]),
                            np.asarray([cert_release.noisy_count]),
                            coordinate_noise_std=aggregate_std,
                            beta_sum=allocation["sum_noise"],
                            beta_count=allocation["count_noise"],
                            beta_sampling=allocation["sampling"],
                            dependence_factor=certification["dependence_factor"],
                            minimum_count_lower=certification[
                                "minimum_noisy_count_lower"
                            ],
                        )
                        lower = float(bound.lower_bound[0])
                        activated = bool(
                            lower >= certification["material_gain_gamma"]
                        )
                        records.append(
                            {
                                "protocol": config["protocol"],
                                "code_commit": code_commit,
                                "config_sha256": sha256(CONFIG_PATH),
                                "real_data_accessed": False,
                                "test_accessed": False,
                                "regime": regime,
                                "seed": seed,
                                "train_epsilon_target": train_epsilon,
                                "cert_epsilon_target": cert_epsilon,
                                "visibility": visibility,
                                "nodes": graph_config["nodes"],
                                "full_edges": len(graph.edges),
                                "train_edges": len(train_edges),
                                "certification_edges": len(cert_edges),
                                "evaluation_edges": len(eval_edges),
                                "training_privacy": asdict(train_calibration),
                                "certification_privacy": asdict(cert_calibration),
                                "training_message_count": training_release.message_count,
                                "certification_message_count": cert_release.message_count,
                                "training_transcript_aggregate_error": training_release.aggregate_error,
                                "certification_transcript_aggregate_error": cert_release.aggregate_error,
                                "certification_empirical_gain": float(
                                    cert_advantages.mean()
                                ),
                                "certificate_lower_bound": lower,
                                "certificate_valid": bool(bound.valid[0]),
                                "activated": activated,
                                "evaluation_gain": evaluation_gain,
                                "policy_evaluation_gain": evaluation_gain
                                if activated
                                else 0.0,
                            }
                        )
    return records


def summarize(config: dict, records: list[dict]) -> dict:
    gate = config["go_no_go_gate"]
    harmful = [record for record in records if record["evaluation_gain"] < 0.0]
    beneficial = [record for record in records if record["evaluation_gain"] > 0.0]
    activated = [record for record in records if record["activated"]]
    harmful_activated = sum(record["activated"] for record in harmful)
    harmful_rate = harmful_activated / len(harmful) if harmful else 1.0
    harmful_upper = (
        one_sided_binomial_upper(harmful_activated, len(harmful))
        if harmful
        else 1.0
    )
    precision = (
        sum(record["evaluation_gain"] > 0 for record in activated) / len(activated)
        if activated
        else 0.0
    )
    oracle_total = sum(max(record["evaluation_gain"], 0.0) for record in records)
    captured = sum(
        max(record["evaluation_gain"], 0.0) for record in activated
    ) / oracle_total if oracle_total else 0.0
    regimes = list(config["graph"]["regimes"])
    regime_means = {
        regime: float(
            np.mean(
                [
                    record["policy_evaluation_gain"]
                    for record in records
                    if record["regime"] == regime
                ]
            )
        )
        for regime in regimes
    }
    seed_means = []
    for seed in range(config["graph"]["seeds"]):
        seed_means.append(
            np.mean(
                [
                    record["policy_evaluation_gain"]
                    for record in records
                    if record["seed"] == seed
                ]
            )
        )
    interval = mean_t_interval(np.asarray(seed_means))
    epsilon_errors = [
        abs(record["training_privacy"]["epsilon"] - record["train_epsilon_target"])
        for record in records
    ] + [
        abs(
            record["certification_privacy"]["epsilon"]
            - record["cert_epsilon_target"]
        )
        for record in records
    ]
    transcript_errors = [
        max(
            record["training_transcript_aggregate_error"],
            record["certification_transcript_aggregate_error"],
        )
        for record in records
    ]
    metrics = {
        "record_count": len(records),
        "harmful_cells": len(harmful),
        "beneficial_cells": len(beneficial),
        "activation_count": len(activated),
        "activation_fraction": len(activated) / len(records),
        "activated_regimes": len({record["regime"] for record in activated}),
        "harmful_activation_rate": harmful_rate,
        "harmful_activation_upper_95": harmful_upper,
        "beneficial_activation_precision": precision,
        "positive_oracle_gain_capture": captured,
        "macro_seed_policy_gain": float(np.mean(seed_means)),
        "macro_seed_policy_gain_95ci": [float(interval[0]), float(interval[1])],
        "worst_regime_mean_policy_gain": min(regime_means.values()),
        "per_regime_mean_policy_gain": regime_means,
        "maximum_transcript_aggregate_error": max(transcript_errors),
        "maximum_accountant_epsilon_error": max(epsilon_errors),
    }
    checks = {
        "harmful_cells_present": metrics["harmful_cells"]
        >= gate["minimum_harmful_cells"],
        "beneficial_cells_present": metrics["beneficial_cells"]
        >= gate["minimum_beneficial_cells"],
        "harmful_activation_rate": metrics["harmful_activation_rate"]
        <= gate["maximum_harmful_activation_rate"],
        "harmful_activation_upper": metrics["harmful_activation_upper_95"]
        <= gate["maximum_harmful_activation_one_sided_95_upper"],
        "beneficial_precision": metrics["beneficial_activation_precision"]
        >= gate["minimum_beneficial_activation_precision"],
        "oracle_capture": metrics["positive_oracle_gain_capture"]
        >= gate["minimum_positive_oracle_gain_capture"],
        "activation_nontrivial": metrics["activation_fraction"]
        >= gate["minimum_activation_fraction"],
        "regime_coverage": metrics["activated_regimes"]
        >= gate["minimum_activated_regimes"],
        "worst_regime_no_harm": metrics["worst_regime_mean_policy_gain"]
        >= gate["minimum_worst_regime_mean_policy_gain"],
        "macro_gain_ci": metrics["macro_seed_policy_gain_95ci"][0] > 0.0,
        "transcript_exact": metrics["maximum_transcript_aggregate_error"]
        <= gate["maximum_transcript_aggregate_error"],
        "accountant_exact": metrics["maximum_accountant_epsilon_error"]
        <= gate["maximum_accountant_epsilon_error"],
        "all_metrics_finite": all(
            np.isfinite(value)
            for value in [
                metrics["activation_fraction"],
                metrics["harmful_activation_rate"],
                metrics["beneficial_activation_precision"],
                metrics["positive_oracle_gain_capture"],
                metrics["macro_seed_policy_gain"],
                metrics["worst_regime_mean_policy_gain"],
                metrics["maximum_transcript_aggregate_error"],
                metrics["maximum_accountant_epsilon_error"],
            ]
        ),
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
        raise SystemExit("R2B output exists; refusing overwrite")
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
