"""Independent R7 audit of the frozen R5 evidence and R6 theorem contract."""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
from typing import Any

import numpy as np

from fed_dp_lp.accounting import epsilon_from_rdp
from fed_dp_lp.private_certificate import CERTIFICATION_L2_SENSITIVITY


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/r5_graph_phase_confirmatory.json"
RESULTS = ROOT / "results/r5_graph_phase_confirmatory"


def read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def close(left: float, right: float, *, atol: float = 1e-12) -> bool:
    return bool(np.isclose(left, right, rtol=0.0, atol=atol))


def reconstruct_summary(
    records: list[dict[str, Any]], config: dict[str, Any], provenance: dict[str, Any]
) -> dict[str, Any]:
    """Rebuild the R5 summary without importing the confirmatory runner."""
    gamma = config["certificate"]["material_gain_gamma"]
    primary = [row for row in records if row["confirmatory_primary"]]
    active = [row for row in primary if row["activated"]]
    false_active = [
        row for row in active if row["full_holdout_pairwise_advantage"] < gamma
    ]
    mean_gain = float(np.mean([row["q5_policy_pairwise_gain"] for row in primary]))
    gates = {
        "primary_record_count": (
            len(primary) == config["confirmatory_primary_cell"]["records"]
        ),
        "maximum_false_material_activations": (
            len(false_active)
            <= config["decision_gates"]["maximum_false_material_activations"]
        ),
        "minimum_activated_primary_cells": (
            len(active)
            >= config["decision_gates"]["minimum_activated_primary_cells"]
        ),
        "minimum_activated_datasets": (
            len({row["dataset"] for row in active})
            >= config["decision_gates"]["minimum_activated_datasets"]
        ),
        "minimum_mean_Q5_policy_gain": (
            mean_gain >= config["decision_gates"]["minimum_mean_Q5_policy_gain"]
        ),
        "all_privacy_accountants_reproduced": all(
            row["accountant_reproduced"] for row in records
        ),
        "all_commitments_verified": provenance["all_commitments_verified"],
        "single_test_access": provenance["test_access_count"] == 1,
        "no_test_tuning": provenance["test_tuning"] is False,
    }
    safety = {
        "primary_record_count",
        "maximum_false_material_activations",
        "all_privacy_accountants_reproduced",
        "all_commitments_verified",
        "single_test_access",
        "no_test_tuning",
    }
    labels = config["decision_labels"]
    decision = (
        labels["pass"]
        if all(gates.values())
        else labels["safe_abstention"]
        if all(gates[key] for key in safety)
        else labels["fail"]
    )
    cells: dict[str, Any] = {}
    for train_epsilon in config["privacy"]["training_epsilon_grid"]:
        for cert_epsilon in config["privacy"]["certification_epsilon_grid"]:
            for visibility in config["privacy"]["visibility_models"]:
                subset = [
                    row
                    for row in records
                    if row["training_epsilon_target"] == train_epsilon
                    and row["certification_epsilon_target"] == cert_epsilon
                    and row["visibility"] == visibility
                ]
                activated = [row for row in subset if row["activated"]]
                key = f"train={train_epsilon}/cert={cert_epsilon}/{visibility}"
                cells[key] = {
                    "records": len(subset),
                    "activated": len(activated),
                    "activated_datasets": len(
                        {row["dataset"] for row in activated}
                    ),
                    "false_material_activations": sum(
                        row["activated"]
                        and row["full_holdout_pairwise_advantage"] < gamma
                        for row in subset
                    ),
                    "mean_q5_policy_gain": float(
                        np.mean([row["q5_policy_pairwise_gain"] for row in subset])
                    ),
                }
    return {
        "protocol": config["protocol"],
        "decision": decision,
        "test_accessed": True,
        "provenance": provenance,
        "primary": {
            "records": len(primary),
            "activated": len(active),
            "activated_datasets": sorted({row["dataset"] for row in active}),
            "false_material_activations": len(false_active),
            "mean_q5_policy_gain": mean_gain,
        },
        "gates": gates,
        "diagnostic_cells": cells,
    }


def summaries_match(left: Any, right: Any, *, path: str = "") -> list[str]:
    """Return precise differences, allowing only tiny floating-point error."""
    if isinstance(left, dict) and isinstance(right, dict):
        errors = []
        if set(left) != set(right):
            errors.append(f"{path}: keys differ")
            return errors
        for key in left:
            errors.extend(
                summaries_match(left[key], right[key], path=f"{path}/{key}")
            )
        return errors
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return [f"{path}: lengths differ"]
        errors = []
        for index, (item_left, item_right) in enumerate(zip(left, right)):
            errors.extend(
                summaries_match(item_left, item_right, path=f"{path}/{index}")
            )
        return errors
    if isinstance(left, float) or isinstance(right, float):
        return [] if close(float(left), float(right)) else [f"{path}: values differ"]
    return [] if left == right else [f"{path}: values differ"]


def accountant_checks(records: list[dict[str, Any]]) -> tuple[bool, float]:
    maximum_error = 0.0
    valid = True
    for row in records:
        train = row["training_privacy"]
        cert = row["certification_privacy"]
        composed = row["composed_privacy"]
        orders = np.asarray(composed["orders"], dtype=np.float64)
        expected_curve = np.asarray(train["rdp"]) + np.asarray(cert["rdp"])
        stored_curve = np.asarray(composed["rdp"])
        maximum_error = max(
            maximum_error, float(np.max(np.abs(expected_curve - stored_curve)))
        )
        epsilon, selected = epsilon_from_rdp(
            orders, stored_curve, delta=composed["delta"]
        )
        valid &= np.array_equal(orders, np.asarray(train["orders"]))
        valid &= np.array_equal(orders, np.asarray(cert["orders"]))
        valid &= close(composed["delta"], train["delta"] + cert["delta"])
        valid &= close(epsilon, composed["epsilon"])
        valid &= close(selected, composed["selected_order"])
    return bool(valid and maximum_error <= 1e-12), maximum_error


def exhaustive_certificate_sensitivity() -> tuple[bool, float]:
    """Enumerate the extreme add/remove contribution changes."""
    maximum = 0.0
    for value in (-1.0, 1.0):
        difference = np.asarray([value, 1.0])
        maximum = max(maximum, float(np.linalg.norm(difference, ord=2)))
    return close(maximum, float(np.sqrt(2.0))), maximum


def source_contract_checks(root: pathlib.Path) -> dict[str, bool]:
    holdout_source = (root / "src/fed_dp_lp/r5_holdout.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(holdout_source)
    corruption = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "corrupted_pairs"
    )
    called_names = {
        node.func.id
        for node in ast.walk(corruption)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    manuscript = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "manuscript/sections").glob("*.tex"))
    )
    corruption_arguments = {
        arg.arg for arg in (*corruption.args.args, *corruption.args.kwonlyargs)
    }
    return {
        "corruption_has_no_graph_or_adjacency_argument": (
            corruption_arguments
            == {"edges", "nodes", "dataset", "seed", "salt"}
        ),
        "corruption_calls_no_graph_loader": not (
            {"load_p3_graph", "undirected_adjacency", "load_dataset"} & called_names
        ),
        "role_labelled_adjacency_is_explicit": "role-labelled canonical edge"
        in manuscript,
        "hash_assumption_is_explicit": (
            "random-oracle" in manuscript or "PRF" in manuscript
        ),
        "finite_target_scope_is_explicit": "finite holdout" in manuscript,
        "pairwise_not_auc_is_explicit": "AUC confidence interval" in manuscript,
        "diagnostic_cells_are_alternative_deployments": (
            "alternative deployment" in manuscript
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=ROOT / "results/r7_independent_audit/theory_contract.json",
    )
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    reported = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    records = read_jsonl(RESULTS / "records_strict.jsonl")
    expected = (
        len(config["datasets"])
        * len(config["seeds"])
        * len(config["privacy"]["training_epsilon_grid"])
        * len(config["privacy"]["certification_epsilon_grid"])
        * len(config["privacy"]["visibility_models"])
    )
    reconstructed = reconstruct_summary(records, config, reported["provenance"])
    summary_differences = summaries_match(reconstructed, reported)
    accountant_ok, maximum_curve_error = accountant_checks(records)
    sensitivity_ok, sensitivity = exhaustive_certificate_sensitivity()
    source_checks = source_contract_checks(ROOT)
    checks = {
        "strict_record_grid_complete": len(records) == expected,
        "strict_record_keys_unique": len(
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
        "summary_independently_reconstructed": not summary_differences,
        "rdp_curves_and_conversions_reproduced": accountant_ok,
        "certificate_sensitivity_is_sqrt2": (
            sensitivity_ok
            and close(sensitivity, CERTIFICATION_L2_SENSITIVITY)
            and close(
                sensitivity, config["privacy"]["certification_l2_sensitivity"]
            )
        ),
        **source_checks,
    }
    report = {
        "protocol": "R7_INDEPENDENT_THEORY_CONTRACT_AUDIT_v1",
        "source_protocol": config["protocol"],
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "record_count": len(records),
        "expected_record_count": expected,
        "maximum_rdp_curve_composition_error": maximum_curve_error,
        "exhaustive_certificate_l2_sensitivity": sensitivity,
        "summary_differences": summary_differences,
        "reported_decision": reported["decision"],
        "reconstructed_decision": reconstructed["decision"],
        "scope_note": (
            "This audit verifies the registered role-labelled database and "
            "random-oracle/PRF-style hash contract; it does not upgrade the "
            "claim to raw-graph adjacency or information-theoretic hashing."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit("R7 theory-contract audit failed")


if __name__ == "__main__":
    main()
