"""Audit P4R RAP synthetic feasibility artifacts."""

import argparse
import hashlib
import json
import pathlib

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p4r_rap_synthetic.json"
OUTPUT = ROOT / "results/p4r_rap_synthetic"


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
    selection = read_jsonl(output / "selection_records.jsonl")
    held = read_jsonl(output / "held_out_records.jsonl")
    summary = json.loads((output / "summary.json").read_text())
    expected_selection = (
        len(config["domains"]) * len(config["seeds"]["selection"])
        * len(config["grid"]["profile_energy_fractions"])
        * len(config["grid"]["profile_weights"])
        * len(config["grid"]["prior_strengths"])
    )
    expected_held = len(config["domains"]) * len(config["seeds"]["held_out"])
    checks = {
        "selection_complete": len(selection) == expected_selection,
        "held_out_complete": len(held) == expected_held,
        "summary_counts_match": summary["selection_record_count"] == expected_selection
        and summary["held_out_record_count"] == expected_held,
        "config_hash_current": all(
            record["config_sha256"] == sha256(config_path) for record in held
        ),
        "sensitivity_sqrt_two": all(
            np.isclose(record["l2_sensitivity"], np.sqrt(2.0)) for record in held
        ),
        "complete_rdp": all(
            len(record["privacy"]["orders"]) == len(record["privacy"]["rdp"])
            and record["privacy"]["steps"] == 1 for record in held
        ),
        "semantic_noise_coupled": all(
            record["semantic_noise_coupled_with_gap"] for record in held
        ),
        "no_real_graph_access": not summary["real_graph_accessed"]
        and all(not record["real_graph_accessed"] for record in held),
        "finite_metrics": all(
            np.isfinite(value) for record in held
            for method in record["metrics"].values()
            for scope in method.values() for value in scope.values()
        ),
    }
    audit = {
        "protocol": config["protocol"] + "_AUDIT",
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "STOP",
        "method_decision": summary["decision"],
        "real_graph_accessed": False,
    }
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
