"""Independently audit P6A records, summaries, hashes, and data boundaries."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p6a_dataset_property_matrix.json"
MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p3_split_audit.json"
PROCESSED = ROOT / "data/processed/p3_benchmark"
OUTPUT = ROOT / "results/p6a_dataset_property_matrix"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in (OUTPUT / "records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    expected = {
        (dataset, seed)
        for dataset in config["development_datasets"]
        for seed in config["development_seeds"]
    }
    observed = {(record["dataset"], record["seed"]) for record in records}
    property_names = list(config["properties"])
    hashes_current = all(
        record["config_sha256"] == sha256(CONFIG_PATH)
        and record["master_config_sha256"] == sha256(MASTER_PATH)
        and record["split_audit_sha256"] == sha256(SPLIT_AUDIT_PATH)
        and record["development_file_sha256"] == sha256(
            PROCESSED / record["dataset"] / f"seed_{record['seed']}_development.npz"
        )
        and record["public_layout_sha256"] == sha256(
            PROCESSED / record["dataset"] / "public_layout.npz"
        )
        for record in records
    )
    summaries_reproduced = True
    for dataset in config["development_datasets"]:
        subset = [record for record in records if record["dataset"] == dataset]
        for name in property_names:
            values = [record["properties"][name] for record in subset]
            registered = summary["datasets"][dataset]["properties"][name]
            summaries_reproduced &= np.isclose(registered["mean"], np.mean(values))
            summaries_reproduced &= np.isclose(
                registered["sample_std"], np.std(values, ddof=1)
            )
    checks = {
        "records_complete_unique": len(records) == config["reporting"]["required_records"]
        and observed == expected,
        "properties_complete_finite": all(
            set(record["properties"]) == set(property_names)
            and all(np.isfinite(value) for value in record["properties"].values())
            for record in records
        ),
        "input_hashes_current": hashes_current,
        "summaries_reproduced": bool(summaries_reproduced),
        "summary_counts_correct": summary["record_count"] == len(records)
        and summary["dataset_count"] == len(config["development_datasets"])
        and summary["seeds_per_dataset"] == len(config["development_seeds"]),
        "prohibited_tests_unaccessed": not summary["test_accessed"]
        and all(not record["test_accessed"] for record in records)
        and json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))["test_decrypted"] is False,
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
        raise SystemExit("P6A audit failed")


if __name__ == "__main__":
    main()
