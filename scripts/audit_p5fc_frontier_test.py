"""Independently audit the one-time P5FC frontier confirmation."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np
from scipy.stats import spearmanr

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.frontier import exact_spearman_permutation_pvalue


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p5fc_fresh_frontier.json"
SOURCE_AUDIT_PATH = ROOT / "data/manifests/p5fc_source_audit.json"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p5fc_split_manifest.json"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p5fc_split_audit.json"
PROCESSED = ROOT / "data/processed/p5fc_frontier"
OUTPUT = ROOT / "results/p5fc_frontier_test"


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
    records = read_jsonl(OUTPUT / "records.jsonl")
    cells = read_jsonl(OUTPUT / "cells.jsonl")
    summary = json.loads((OUTPUT / "summary.json").read_text())
    access = json.loads((OUTPUT / "access.json").read_text())
    gate = config["confirmatory_gate"]
    expected_keys = {
        (dataset, seed, float(epsilon), visibility)
        for dataset in config["datasets"]
        for seed in config["split"]["seeds"]
        for epsilon in config["privacy"]["epsilon_grid"]
        for visibility in config["privacy"]["visibility_models"]
    }
    actual_keys = {
        (
            record["dataset"], record["seed"],
            float(record["epsilon_target"]), record["visibility"],
        )
        for record in records
    }

    calibrations = {
        float(epsilon): calibrate_gaussian(
            target_epsilon=epsilon,
            delta=config["privacy"]["delta"],
            sensitivity=np.sqrt(2.0),
            steps=config["release"]["hops"],
            orders=DEFAULT_ORDERS,
        )
        for epsilon in config["privacy"]["epsilon_grid"]
    }

    def calibration_matches(record: dict) -> bool:
        expected = calibrations[float(record["epsilon_target"])]
        actual = record["privacy"]
        return (
            np.isclose(actual["epsilon"], expected.epsilon)
            and np.isclose(actual["delta"], expected.delta)
            and np.isclose(actual["sensitivity"], expected.sensitivity)
            and np.isclose(actual["noise_std"], expected.noise_std)
            and actual["steps"] == expected.steps
            and np.isclose(actual["selected_order"], expected.selected_order)
            and np.allclose(actual["orders"], expected.orders)
            and np.allclose(actual["rdp"], expected.rdp)
        )

    expected_cell_keys = {
        (dataset, float(epsilon), visibility)
        for dataset in config["datasets"]
        for epsilon in config["privacy"]["epsilon_grid"]
        for visibility in config["privacy"]["visibility_models"]
    }
    actual_cell_keys = {
        (cell["dataset"], float(cell["epsilon"]), cell["visibility"])
        for cell in cells
    }
    pooled_rho = float(spearmanr(
        [cell["mean_log10_frontier_signal_ratio"] for cell in cells],
        [cell["mean_global_auc_gain"] for cell in cells],
    ).statistic)
    per_dataset = {}
    for dataset in config["datasets"]:
        subset = [cell for cell in cells if cell["dataset"] == dataset]
        rho, pvalue = exact_spearman_permutation_pvalue(
            np.asarray([cell["mean_log10_frontier_signal_ratio"] for cell in subset]),
            np.asarray([cell["mean_global_auc_gain"] for cell in subset]),
        )
        per_dataset[dataset] = (rho, pvalue)

    energy_pairs = {}
    for record in records:
        key = (record["dataset"], record["seed"], record["epsilon_target"])
        energy_pairs.setdefault(key, {})[record["visibility"]] = record[
            "expected_first_hop_noise_energy"
        ]

    development_hashes = {}
    for dataset in config["datasets"]:
        for seed in config["split"]["seeds"]:
            path = PROCESSED / dataset / f"seed_{seed}_development.npz"
            development_hashes[(dataset, seed)] = sha256(path)

    checks = {
        "single_access_record": access["test_access_count"] == 1
        and summary["test_access_count"] == 1
        and all(record["test_access_count"] == 1 for record in records),
        "records_complete_unique": len(records) == gate["expected_records"]
        and actual_keys == expected_keys,
        "cells_complete_unique": len(cells) == gate["expected_aggregate_cells"]
        and actual_cell_keys == expected_cell_keys
        and all(cell["seeds"] == len(config["split"]["seeds"]) for cell in cells),
        "artifact_hashes_current": all(
            record["config_sha256"] == sha256(CONFIG_PATH)
            and record["source_audit_sha256"] == sha256(SOURCE_AUDIT_PATH)
            and record["split_manifest_sha256"] == sha256(SPLIT_MANIFEST_PATH)
            and record["split_audit_sha256"] == sha256(SPLIT_AUDIT_PATH)
            and record["development_file_sha256"]
            == development_hashes[(record["dataset"], record["seed"])]
            for record in records
        ),
        "encoding_caches_current": all(
            (ROOT / record["public_encoding_cache"]).exists()
            and record["public_encoding_cache_sha256"]
            == sha256(ROOT / record["public_encoding_cache"])
            for record in records
        ),
        "sensitivity_and_complete_rdp": all(
            np.isclose(record["l2_sensitivity_per_release"], np.sqrt(2.0))
            and record["release_count"] == config["release"]["hops"]
            and len(record["privacy"]["orders"]) == len(record["privacy"]["rdp"])
            and calibration_matches(record)
            for record in records
        ),
        "noise_energy_ratio": all(
            set(pair) == set(config["privacy"]["visibility_models"])
            and np.isclose(
                pair["visible_messages"] / pair["ideal_secagg"],
                gate["required_noise_energy_ratio_visible_over_ideal"],
            )
            for pair in energy_pairs.values()
        ),
        "degree_bound": all(
            record["frontier_signal_ratio"]
            <= record["frontier_degree_upper_ratio"] + 1e-12
            for record in records
        ),
        "finite": all(
            np.isfinite([
                record["frontier_signal_ratio"],
                record["frontier_degree_upper_ratio"],
                *record["noise_norm_interval_95"],
                *record["metrics"]["gap_style"].values(),
                *record["metrics"]["public_cosine"].values(),
                *record["metrics"]["gain_over_public"].values(),
            ]).all()
            for record in records
        ),
        "pooled_statistic_reproduced": np.isclose(
            pooled_rho, summary["pooled_cell_spearman"]
        ),
        "dataset_statistics_reproduced": all(
            np.isclose(rho, summary["per_dataset"][dataset]["spearman"])
            and np.isclose(
                pvalue,
                summary["per_dataset"][dataset][
                    "exact_two_sided_permutation_pvalue"
                ],
            )
            for dataset, (rho, pvalue) in per_dataset.items()
        ),
        "runner_checks_pass": all(summary["checks"].values()),
    }
    audit = {
        "schema_version": 1,
        "protocol": "P5FC_FRESH_SOURCE_FRONTIER_CONFIRMATION_v1_AUDIT",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "confirmatory_decision": summary["decision"],
        "test_access_count": 1,
    }
    (OUTPUT / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
