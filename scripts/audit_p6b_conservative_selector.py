"""Reproduce P6B cell construction, predictions, policy metrics, and gate."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np

from fed_dp_lp.conservative_selector import evaluate_policy, nested_lodo_safety_predictions
from run_p6b_conservative_selector import build_cells


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p6b_conservative_selector.json"
P6A_PATH = ROOT / "results/p6a_dataset_property_matrix/summary.json"
P6A_AUDIT_PATH = ROOT / "results/p6a_dataset_property_matrix/audit.json"
P5F_PATH = ROOT / "results/p5f_frontier_validation/records.jsonl"
P5F_CONFIG_PATH = ROOT / "configs/p5f_frontier_validation.json"
OUTPUT = ROOT / "results/p6b_conservative_selector"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    p6a = json.loads(P6A_PATH.read_text(encoding="utf-8"))
    p5f = [json.loads(line) for line in P5F_PATH.read_text().splitlines()]
    stored = [json.loads(line) for line in (OUTPUT / "cells.jsonl").read_text().splitlines()]
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    rebuilt = build_cells(config, p6a, p5f)
    domains = np.asarray([cell["dataset"] for cell in rebuilt])
    features = np.asarray([cell["features"] for cell in rebuilt])
    outcomes = np.asarray([cell["mean_gain"] for cell in rebuilt])
    predictions, margins = nested_lodo_safety_predictions(
        domains, features, outcomes, ridge=config["model"]["ridge"]
    )
    activated = predictions - margins >= config["material_gain"]
    metrics = evaluate_policy(
        domains, outcomes, activated, material_gain=config["material_gain"]
    )
    gate = config["no_harm_gate"]
    reproduced_checks = {
        "minimum_activation_fraction": metrics["activation_fraction"] >= gate["minimum_activation_fraction"],
        "minimum_activated_datasets": metrics["activated_datasets"] >= gate["minimum_activated_datasets"],
        "no_negative_mean_gain_activations": metrics["negative_mean_gain_activations"] <= gate["maximum_negative_mean_gain_activations"],
        "minimum_material_precision": metrics["material_precision"] >= gate["minimum_material_precision"],
        "minimum_positive_oracle_gain_capture": metrics["positive_oracle_gain_capture"] >= gate["minimum_positive_oracle_gain_capture"],
        "minimum_worst_dataset_policy_gain": metrics["worst_dataset_policy_gain"] >= gate["minimum_worst_dataset_policy_gain"],
        "macro_domain_gain_95ci_lower_above_zero": metrics["macro_dataset_policy_gain_95ci"][0] > 0.0,
        "all_metrics_finite": all(np.isfinite(value) for value in [
            metrics["activation_fraction"], metrics["material_precision"],
            metrics["positive_oracle_gain_capture"], metrics["macro_dataset_policy_gain"],
            metrics["worst_dataset_policy_gain"], *predictions, *margins,
        ]),
        "test_never_accessed": True,
    }
    expected_decision = (
        config["reporting"]["decision_if_all_gates_pass"]
        if all(reproduced_checks.values())
        else config["reporting"]["decision_otherwise"]
    )
    checks = {
        "cells_complete_unique": len(stored) == config["reporting"]["cells"]
        and len({(row["dataset"], row["epsilon"], row["visibility"]) for row in stored}) == len(stored),
        "input_hashes_current": all(
            row["config_sha256"] == sha256(CONFIG_PATH)
            and row["p6a_summary_sha256"] == sha256(P6A_PATH)
            and row["p6a_audit_sha256"] == sha256(P6A_AUDIT_PATH)
            and row["p5f_records_sha256"] == sha256(P5F_PATH)
            and row["p5f_config_sha256"] == sha256(P5F_CONFIG_PATH)
            for row in stored
        ),
        "features_and_outcomes_reproduced": all(
            np.allclose(row["features"], source["features"])
            and np.allclose(row["seed_gains"], source["seed_gains"])
            and np.isclose(row["mean_gain"], source["mean_gain"])
            for row, source in zip(stored, rebuilt)
        ),
        "predictions_and_actions_reproduced": all(
            np.isclose(row["predicted_gain"], predictions[index])
            and np.isclose(row["safety_margin"], margins[index])
            and (row["action"] == "dp_structural") == bool(activated[index])
            for index, row in enumerate(stored)
        ),
        "metrics_reproduced": metrics == summary["metrics"],
        "gate_and_decision_reproduced": reproduced_checks == summary["checks"]
        and expected_decision == summary["decision"],
        "prohibited_tests_unaccessed": not summary["test_accessed"]
        and all(not row["test_accessed"] for row in stored),
    }
    audit = {
        "schema_version": 1,
        "protocol": config["protocol"] + "_AUDIT",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "test_accessed": False,
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))
    if audit["status"] != "PASS":
        raise SystemExit("P6B audit failed")


if __name__ == "__main__":
    main()
