"""Audit the R5 preregistration without decrypting any sealed test payload."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/r5_graph_phase_confirmatory.json"
P3_MASTER = ROOT / "configs/p3_master_benchmark.json"
P3_SELECTION = ROOT / "results/p3_gap_validation/summary.json"
SPLIT_MANIFEST = ROOT / "data/manifests/p3_split_manifest.json"
SPLIT_AUDIT = ROOT / "data/manifests/p3_split_audit.json"
SEALED = ROOT / "data/sealed/p3_benchmark"
OUTPUT = ROOT / "results/r5_preregistration_audit"


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


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    master = json.loads(P3_MASTER.read_text(encoding="utf-8"))
    selection = json.loads(P3_SELECTION.read_text(encoding="utf-8"))
    manifest = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT.read_text(encoding="utf-8"))

    frozen = config["candidate"]["selected_validation_hyperparameters"]
    observed = {
        dataset: {
            "projection_dimension": int(values["selected"]["projection_dimension"]),
            "hops": int(values["selected"]["hops"]),
        }
        for dataset, values in selection["selections"].items()
    }
    manifest_records = {
        (dataset["dataset"], record["seed"]): record
        for dataset in manifest["datasets"]
        for record in dataset["splits"]
    }
    sealed_checks = {}
    for dataset in config["datasets"]:
        for seed in config["seeds"]:
            path = SEALED / f"{dataset}_seed_{seed}.fernet"
            expected = manifest_records[(dataset, seed)]["commitments"][
                "sealed_payload_sha256"
            ]
            sealed_checks[f"{dataset}/{seed}"] = path.exists() and sha256(path) == expected

    checks = {
        "config_status_frozen": config["status"].startswith("frozen_before"),
        "dataset_order_matches_p3": config["datasets"] == master["datasets"],
        "seed_order_matches_p3": config["seeds"] == master["split"]["seeds"],
        "candidate_selection_exact": frozen == observed,
        "selection_used_validation_only": selection["test_accessed"] is False,
        "split_audit_pass": split_audit["status"] == "PASS",
        "split_audit_never_decrypted": split_audit["test_decrypted"] is False,
        "manifest_test_untouched": (
            manifest["test_status"] == "encrypted_never_accessed"
            and manifest["test_access_count"] == 0
        ),
        "all_30_sealed_payloads_match": (
            len(sealed_checks) == 30 and all(sealed_checks.values())
        ),
        "validation_not_registered_as_certificate": (
            config["sealed_holdout_partition"]["source"]
            == "original P3 encrypted test positives"
        ),
        "conservative_rdp_composition": config["privacy"]["composition"].startswith(
            "conservative sequential RDP composition"
        ),
        "counterfactual_grid_disclosed": "alternative deployment"
        in config["privacy"]["counterfactual_cells"],
        "candidate_not_mislabeled_official": (
            config["candidate"]["official_reproduction"] is False
        ),
    }
    payload = {
        "protocol": config["protocol"],
        "code_commit": git_head(),
        "test_accessed": False,
        "hashes": {
            "r5_config_sha256": sha256(CONFIG),
            "p3_master_sha256": sha256(P3_MASTER),
            "p3_selection_sha256": sha256(P3_SELECTION),
            "p3_split_manifest_sha256": sha256(SPLIT_MANIFEST),
            "p3_split_audit_sha256": sha256(SPLIT_AUDIT),
        },
        "checks": checks,
        "sealed_checks": sealed_checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / "audit.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(path)
    if payload["status"] != "PASS":
        raise SystemExit("R5 preregistration audit failed")


if __name__ == "__main__":
    main()
