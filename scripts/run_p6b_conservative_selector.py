"""Evaluate the frozen P6B conservative selector on development evidence."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

import numpy as np

from fed_dp_lp.conservative_selector import (
    evaluate_policy,
    nested_lodo_safety_predictions,
)


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


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def build_cells(config: dict, p6a: dict, records: list[dict]) -> list[dict]:
    cells: list[dict] = []
    for dataset in config["datasets"]:
        props = p6a["datasets"][dataset]["properties"]
        public_auc = props["public_feature_auc"]["mean"]
        headroom = 1.0 - public_auc
        cn_advantage = props["common_neighbor_auc"]["mean"] - public_auc
        hub_dominance = max(
            0.0,
            props["preferential_attachment_auc"]["mean"]
            - props["common_neighbor_auc"]["mean"],
        )
        missing = 1.0 - props["public_feature_coverage"]["mean"]
        for epsilon in config["epsilon_grid"]:
            for visibility in config["visibility_models"]:
                subset = [
                    row for row in records
                    if row["dataset"] == dataset
                    and row["epsilon_target"] == epsilon
                    and row["visibility"] == visibility
                ]
                if len(subset) != 5:
                    raise RuntimeError(f"incomplete P5F cell: {dataset}/{epsilon}/{visibility}")
                signal = float(np.mean([row["frontier_signal_ratio"] for row in subset]))
                recoverability = signal / (1.0 + signal)
                gains = [row["metrics"]["gain_over_public"]["global"] for row in subset]
                features = [
                    recoverability,
                    headroom,
                    cn_advantage,
                    hub_dominance,
                    missing,
                    recoverability * headroom,
                    recoverability * cn_advantage,
                ]
                cells.append({
                    "dataset": dataset,
                    "epsilon": epsilon,
                    "visibility": visibility,
                    "features": features,
                    "feature_values": dict(zip(config["features"], features)),
                    "seed_gains": gains,
                    "mean_gain": float(np.mean(gains)),
                })
    return cells


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("P6B output exists; refusing overwrite")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    p6a = json.loads(P6A_PATH.read_text(encoding="utf-8"))
    p6a_audit = json.loads(P6A_AUDIT_PATH.read_text(encoding="utf-8"))
    if p6a_audit["status"] != "PASS" or p6a_audit["test_accessed"]:
        raise SystemExit("P6A evidence is not clean")
    records = [json.loads(line) for line in P5F_PATH.read_text().splitlines()]
    if any(row["split"] != "validation" or row["test_accessed"] for row in records):
        raise SystemExit("P5F input is not validation-only")
    cells = build_cells(config, p6a, records)
    domains = np.asarray([cell["dataset"] for cell in cells])
    features = np.asarray([cell["features"] for cell in cells])
    outcomes = np.asarray([cell["mean_gain"] for cell in cells])
    predictions, margins = nested_lodo_safety_predictions(
        domains, features, outcomes, ridge=config["model"]["ridge"]
    )
    lower_predictions = predictions - margins
    activated = lower_predictions >= config["material_gain"]
    metrics = evaluate_policy(
        domains, outcomes, activated, material_gain=config["material_gain"]
    )
    for index, cell in enumerate(cells):
        cell.update({
            "protocol": config["protocol"],
            "code_commit": git_head(),
            "test_accessed": False,
            "config_sha256": sha256(CONFIG_PATH),
            "p6a_summary_sha256": sha256(P6A_PATH),
            "p6a_audit_sha256": sha256(P6A_AUDIT_PATH),
            "p5f_records_sha256": sha256(P5F_PATH),
            "p5f_config_sha256": sha256(P5F_CONFIG_PATH),
            "predicted_gain": float(predictions[index]),
            "safety_margin": float(margins[index]),
            "conservative_lower_prediction": float(lower_predictions[index]),
            "action": "dp_structural" if activated[index] else "public_only",
            "policy_mean_gain": float(outcomes[index] if activated[index] else 0.0),
        })
    gate = config["no_harm_gate"]
    checks = {
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
    decision = (
        config["reporting"]["decision_if_all_gates_pass"]
        if all(checks.values())
        else config["reporting"]["decision_otherwise"]
    )
    summary = {
        "protocol": config["protocol"],
        "cell_count": len(cells),
        "decision": decision,
        "checks": checks,
        "metrics": metrics,
        "test_accessed": False,
    }
    OUTPUT.mkdir(parents=True)
    with (OUTPUT / "cells.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for cell in cells:
            handle.write(json.dumps(cell, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
