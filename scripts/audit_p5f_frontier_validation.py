"""Audit the frozen P5F privacy-utility frontier validation artifacts."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p5f_frontier_validation.json"
MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p3_split_manifest.json"
OUTPUT = ROOT / "results/p5f_frontier_validation"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    records = read_jsonl(OUTPUT / "records.jsonl")
    cells = read_jsonl(OUTPUT / "cells.jsonl")
    summary = json.loads((OUTPUT / "summary.json").read_text())
    expected_records = (
        len(master["datasets"])
        * len(master["split"]["seeds"])
        * len(config["epsilon_grid"])
        * len(config["visibility_models"])
    )
    expected_cells = (
        len(master["datasets"])
        * len(config["epsilon_grid"])
        * len(config["visibility_models"])
    )

    recalibrations = {}
    for epsilon in config["epsilon_grid"]:
        for hops in {item["hops"] for item in config["frozen_gap_backbones"].values()}:
            recalibrations[(float(epsilon), hops)] = calibrate_gaussian(
                target_epsilon=epsilon,
                delta=config["privacy"]["delta"],
                sensitivity=np.sqrt(2.0),
                steps=hops,
                orders=DEFAULT_ORDERS,
            )

    unique_keys = {
        (r["dataset"], r["seed"], r["epsilon_target"], r["visibility"])
        for r in records
    }
    energy_pairs = {}
    for record in records:
        key = (record["dataset"], record["seed"], record["epsilon_target"])
        energy_pairs.setdefault(key, {})[record["visibility"]] = record[
            "expected_first_hop_noise_energy"
        ]

    def calibration_matches(record: dict) -> bool:
        expected = recalibrations[(float(record["epsilon_target"]), record["release_count"])]
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

    def backbone_matches(record: dict) -> bool:
        frozen = config["frozen_gap_backbones"][record["dataset"]]
        cache_path = ROOT / record["public_encoding_cache"]
        with np.load(cache_path, allow_pickle=False) as cached:
            requested = int(cached["requested_dimension"])
            actual = int(cached["encoded"].shape[1])
        return (
            requested == frozen["projection_dimension"]
            and actual == record["projection_dimension"]
            and record["release_count"] == frozen["hops"]
        )

    expected_ratio = config["analysis_gate"][
        "required_noise_energy_ratio_visible_over_ideal"
    ]
    checks = {
        "records_complete_unique": len(records) == expected_records
        and len(unique_keys) == expected_records
        and summary["record_count"] == expected_records,
        "cells_complete": len(cells) == expected_cells
        and summary["cell_count"] == expected_cells,
        "datasets_seeds_budgets_visibility_exact": {
            r["dataset"] for r in records
        } == set(master["datasets"])
        and {r["seed"] for r in records} == set(master["split"]["seeds"])
        and {float(r["epsilon_target"]) for r in records}
        == {float(x) for x in config["epsilon_grid"]}
        and {r["visibility"] for r in records}
        == set(config["visibility_models"]),
        "test_never_accessed": not summary["test_accessed"]
        and all(not r["test_accessed"] and r["split"] == "validation" for r in records),
        "artifact_hashes_current": all(
            r["config_sha256"] == sha256(CONFIG_PATH)
            and r["master_config_sha256"] == sha256(MASTER_PATH)
            and r["split_manifest_sha256"] == sha256(SPLIT_MANIFEST_PATH)
            for r in records
        ),
        "public_encoding_caches_current": all(
            (ROOT / r["public_encoding_cache"]).exists()
            and r["public_encoding_cache_sha256"]
            == sha256(ROOT / r["public_encoding_cache"])
            for r in records
        ),
        "sensitivity_and_complete_rdp": all(
            np.isclose(r["l2_sensitivity_per_release"], np.sqrt(2.0))
            and len(r["privacy"]["orders"]) == len(r["privacy"]["rdp"])
            and r["privacy"]["steps"] == r["release_count"]
            and calibration_matches(r)
            for r in records
        ),
        "frozen_backbones": all(backbone_matches(r) for r in records),
        "degree_bound_dominates_signal": all(
            r["frontier_signal_ratio"] <= r["frontier_degree_upper_ratio"] + 1e-12
            for r in records
        ),
        "noise_intervals_ordered": all(
            0 <= r["noise_norm_interval_95"][0]
            < r["noise_norm_interval_95"][1]
            for r in records
        ),
        "visible_ideal_energy_ratio": len(energy_pairs)
        == expected_records // len(config["visibility_models"])
        and all(
            set(pair) == set(config["visibility_models"])
            and np.isclose(
                pair["visible_messages"] / pair["ideal_secagg"], expected_ratio
            )
            for pair in energy_pairs.values()
        ),
        "visible_prior_exact_reproduction": summary[
            "max_visible_reproduction_auc_error"
        ]
        <= config["analysis_gate"]["maximum_visible_reproduction_auc_error"],
        "finite_frontier_and_metrics": all(
            np.isfinite(
                [
                    r["frontier_signal_ratio"],
                    r["frontier_degree_upper_ratio"],
                    r["expected_first_hop_noise_energy"],
                    *r["noise_norm_interval_95"],
                    *r["metrics"]["gap_style"].values(),
                    *r["metrics"]["public_cosine"].values(),
                    *r["metrics"]["gain_over_public"].values(),
                ]
            ).all()
            for r in records
        ),
        "runner_checks_pass": all(summary["checks"].values()),
    }
    audit = {
        "protocol": f'{config["protocol"]}_AUDIT',
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "frontier_decision": summary["decision"],
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
