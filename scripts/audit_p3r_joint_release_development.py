"""Audit P3R-v2 completeness, privacy metadata, and frozen provenance."""

import argparse
import hashlib
import json
import pathlib

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER = json.loads((ROOT / "configs/p3_master_benchmark.json").read_text())
CONFIG_PATH = ROOT / "configs/p3r_joint_release_development.json"
CONFIG = json.loads(CONFIG_PATH.read_text())
OUTPUT = ROOT / "results/p3r_joint_release_development"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=pathlib.Path, default=CONFIG_PATH)
    parser.add_argument("--output", type=pathlib.Path, default=OUTPUT)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    output = args.output if args.output.is_absolute() else ROOT / args.output
    config = json.loads(config_path.read_text())
    grid = read_jsonl(output / "grid_records.jsonl")
    held = read_jsonl(output / "held_out_records.jsonl")
    summary = json.loads((output / "summary.json").read_text())
    candidate = config["candidate"]
    expected_grid = (
        len(MASTER["datasets"]) * len(MASTER["split"]["seeds"])
        * len(candidate["histogram_energy_fractions"])
        * len(candidate["residual_weights"])
    )
    expected_held = len(MASTER["datasets"]) * len(MASTER["split"]["seeds"])
    expected_backbones = candidate["frozen_gap_backbones"]
    labels = config.get("decision_labels", {})
    checks = {
        "grid_complete": len(grid) == expected_grid,
        "held_out_complete": len(held) == expected_held,
        "summary_counts_match": summary["grid_record_count"] == expected_grid
        and summary["held_out_record_count"] == expected_held,
        "test_never_accessed": not summary["test_accessed"]
        and all(not record["test_accessed"] for record in held),
        "config_hash_current": all(
            record["p3r_config_sha256"] == sha256(config_path) for record in held
        ),
        "sensitivity_sqrt_two": all(
            np.isclose(record["l2_sensitivity_per_release"], np.sqrt(2.0))
            for record in held
        ),
        "joint_scale_identity": all(
            np.isclose(record["selected_config"]["scale_identity"], 2.0)
            for record in held
        ),
        "complete_rdp": all(
            len(record["privacy"]["orders"]) == len(record["privacy"]["rdp"])
            and len(record["privacy"]["orders"]) > 1
            and record["privacy"]["steps"] == record["release_count"]
            for record in held
        ),
        "frozen_gap_backbones": all(
            record["selected_config"]["projection_dimension_requested"]
            == expected_backbones[record["dataset"]]["projection_dimension"]
            and record["selected_config"]["hops"]
            == expected_backbones[record["dataset"]]["hops"]
            for record in held
        ),
        "visible_message_model": all(
            record["visibility"] == "individually_visible_client_messages"
            and record["server_sum_simulation"]
            == "distribution_equivalent_sqrt_K_gaussian"
            for record in held
        ),
        "finite_metrics": all(
            np.isfinite(value) for record in held
            for method in record["metrics"].values()
            for scope in method.values() for value in scope.values()
        ),
        "decision_preserved": summary["decision"] in {
            labels.get("pass", "GO_TO_FRESH_CONFIRMATORY_PROTOCOL"),
            labels.get("fail", "NO_GO_REJECT_JOINT_RELEASE_CANDIDATE"),
        },
    }
    audit = {
        "protocol": summary["protocol"] + "_AUDIT",
        "expected_grid_records": expected_grid,
        "expected_held_out_records": expected_held,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "method_decision": summary["decision"],
        "test_accessed": False,
    }
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
