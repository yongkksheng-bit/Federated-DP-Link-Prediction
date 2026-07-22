"""Audit P5C2 development artifacts and independently reproduce its gate."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np

from fed_dp_lp.phase_diagram import (
    leave_one_dataset_out_predictions,
    prediction_metrics,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p5c2_phase_diagram_development.json"
MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
P5F_CONFIG_PATH = ROOT / "configs/p5f_frontier_validation.json"
P5F_RECORDS_PATH = ROOT / "results/p5f_frontier_validation/records.jsonl"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p3_split_manifest.json"
PROCESSED = ROOT / "data/processed/p3_benchmark"
OUTPUT = ROOT / "results/p5c2_phase_diagram_development"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    p5f_config = json.loads(P5F_CONFIG_PATH.read_text(encoding="utf-8"))
    proxies = read_jsonl(OUTPUT / "proxy_records.jsonl")
    cells = read_jsonl(OUTPUT / "phase_cells.jsonl")
    summary = json.loads((OUTPUT / "summary.json").read_text())
    gate = config["go_no_go"]
    expected_proxy_keys = {
        (dataset, seed) for dataset in config["datasets"] for seed in config["seeds"]
    }
    actual_proxy_keys = {(record["dataset"], record["seed"]) for record in proxies}
    expected_cell_keys = {
        (dataset, epsilon, visibility)
        for dataset in config["datasets"]
        for epsilon in p5f_config["epsilon_grid"]
        for visibility in p5f_config["visibility_models"]
    }
    actual_cell_keys = {
        (cell["dataset"], cell["epsilon"], cell["visibility"])
        for cell in cells
    }
    cache_hashes = {
        path: sha256(ROOT / path)
        for path in {record["public_encoding_cache"] for record in proxies}
    }
    development_hashes = {
        (dataset, seed): sha256(
            PROCESSED / dataset / f"seed_{seed}_development.npz"
        )
        for dataset, seed in expected_proxy_keys
    }

    datasets = np.asarray([cell["dataset"] for cell in cells])
    recoverability = np.asarray([cell["energy_recoverability"] for cell in cells])
    alignment = np.asarray([
        cell["alignment_clean_fusion_gain_cv"] for cell in cells
    ])
    outcome = np.asarray([cell["outcome_global_auc_gain"] for cell in cells])
    one_features = np.column_stack([recoverability, recoverability**2])
    two_features = np.column_stack([
        recoverability,
        recoverability**2,
        alignment,
        recoverability * alignment,
    ])
    ridge = config["phase_model"]["ridge"]
    one_predictions = leave_one_dataset_out_predictions(
        datasets, one_features, outcome, ridge=ridge
    )
    two_predictions = leave_one_dataset_out_predictions(
        datasets, two_features, outcome, ridge=ridge
    )
    one_metrics = prediction_metrics(outcome, one_predictions)
    two_metrics = prediction_metrics(outcome, two_predictions)
    per_dataset = {}
    for dataset in config["datasets"]:
        mask = datasets == dataset
        one_mae = float(np.mean(np.abs(outcome[mask] - one_predictions[mask])))
        two_mae = float(np.mean(np.abs(outcome[mask] - two_predictions[mask])))
        per_dataset[dataset] = (one_mae, two_mae)
    relative_reduction = (one_metrics["mae"] - two_metrics["mae"]) / one_metrics["mae"]
    recomputed_gate = {
        "proxy_records_complete": len(proxies) == gate["expected_proxy_records"],
        "phase_cells_complete": len(cells) == gate["expected_phase_cells"]
        and all(cell["seeds"] == len(config["seeds"]) for cell in cells),
        "relative_mae_reduction": relative_reduction
        >= gate["minimum_relative_lodo_mae_reduction"],
        "sign_accuracy": two_metrics["sign_accuracy"]
        >= gate["minimum_lodo_sign_accuracy"],
        "prediction_spearman": two_metrics["spearman"]
        >= gate["minimum_lodo_prediction_spearman"],
        "datasets_improved": sum(two < one for one, two in per_dataset.values())
        >= gate["minimum_datasets_with_lower_mae"],
        "worst_dataset_degradation": max(
            two - one for one, two in per_dataset.values()
        ) <= gate["maximum_any_dataset_mae_degradation"],
        "finite": np.isfinite([
            *one_predictions, *two_predictions, *outcome, *alignment, *recoverability
        ]).all(),
        "test_never_accessed": all(not record["test_accessed"] for record in proxies),
    }
    recomputed_gate = {name: bool(value) for name, value in recomputed_gate.items()}
    expected_decision = (
        "ADVANCE_TWO_AXIS_TO_NEW_SOURCE_CONFIRMATION"
        if all(recomputed_gate.values())
        else "REJECT_TWO_AXIS_PHASE_PROXY"
    )
    checks = {
        "proxy_records_complete_unique": len(proxies) == gate["expected_proxy_records"]
        and actual_proxy_keys == expected_proxy_keys,
        "phase_cells_complete_unique": len(cells) == gate["expected_phase_cells"]
        and actual_cell_keys == expected_cell_keys,
        "input_hashes_current": all(
            record["config_sha256"] == sha256(CONFIG_PATH)
            and record["master_config_sha256"] == sha256(MASTER_PATH)
            and record["p5f_config_sha256"] == sha256(P5F_CONFIG_PATH)
            and record["p5f_records_sha256"] == sha256(P5F_RECORDS_PATH)
            and record["p3_split_manifest_sha256"] == sha256(SPLIT_MANIFEST_PATH)
            and record["development_file_sha256"]
            == development_hashes[(record["dataset"], record["seed"])]
            for record in proxies
        ),
        "encoding_caches_current": all(
            record["public_encoding_cache_sha256"]
            == cache_hashes[record["public_encoding_cache"]]
            for record in proxies
        ),
        "probe_counts_matched": all(
            record["probe_positive_count"] == record["probe_negative_count"]
            and record["probe_positive_count"] > 0
            for record in proxies
        ),
        "finite_proxy_metrics": all(
            np.isfinite([
                *record["metrics"]["public_auc"].values(),
                *record["metrics"]["clean_structural_auc"].values(),
                *record["metrics"]["clean_fusion_auc"].values(),
                *record["metrics"]["clean_fusion_gain_cv"].values(),
                *record["metrics"]["clean_structural_gain_cv"].values(),
                record["metrics"]["clean_fusion_margin_gain_cv"],
                record["metrics"]["normalized_structural_effective_rank"],
                record["metrics"]["training_degree_coefficient_of_variation"],
            ]).all()
            for record in proxies
        ),
        "predictions_reproduced": np.allclose(
            one_predictions,
            [cell["one_axis_lodo_prediction"] for cell in cells],
        ) and np.allclose(
            two_predictions,
            [cell["two_axis_lodo_prediction"] for cell in cells],
        ),
        "metrics_reproduced": all(
            np.isclose(one_metrics[name], summary["one_axis_lodo"][name])
            and np.isclose(two_metrics[name], summary["two_axis_lodo"][name])
            for name in one_metrics
        ) and np.isclose(relative_reduction, summary["relative_mae_reduction"]),
        "gate_reproduced": recomputed_gate == summary["checks"],
        "decision_consistent": summary["decision"] == expected_decision,
        "prohibited_tests_unaccessed": all(
            not record["test_accessed"]
            and record["split"] == "training_internal_cross_fit"
            for record in proxies
        ) and not summary["test_accessed"],
    }
    checks = {name: bool(value) for name, value in checks.items()}
    audit = {
        "schema_version": 1,
        "protocol": "P5C2_TWO_AXIS_PHASE_DIAGRAM_DEVELOPMENT_v1_AUDIT",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "development_decision": summary["decision"],
        "test_accessed": False,
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
