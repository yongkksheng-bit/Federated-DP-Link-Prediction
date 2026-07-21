"""Prepare P5FC development arrays and immediately seal fresh tests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
from datetime import datetime, timezone

import numpy as np
from cryptography.fernet import Fernet

from fed_dp_lp.p2_data import balanced_sha256_homes
from fed_dp_lp.p2_sealing import array_commitment, encrypted_npz
from fed_dp_lp.p5fc_data import (
    capped_stratified_positive_split,
    canonical_undirected_edges,
    load_graphsaint_adjacency,
    sample_stratified_nonedges,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p5fc_fresh_frontier.json"
SOURCE_AUDIT_PATH = ROOT / "data/manifests/p5fc_source_audit.json"
RAW = ROOT / "data/raw/p5fc"
PROCESSED = ROOT / "data/processed/p5fc_frontier"
SEALED = ROOT / "data/sealed/p5fc_frontier"
MANIFEST_PATH = ROOT / "data/manifests/p5fc_split_manifest.json"


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


def strata(pairs: np.ndarray, homes: np.ndarray) -> dict[str, int]:
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    return {"intra": int(np.sum(~cross)), "cross": int(np.sum(cross))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initialize-sealed-confirmation", action="store_true")
    args = parser.parse_args()
    if not args.initialize_sealed_confirmation:
        raise SystemExit("explicit sealed-confirmation initialization is required")
    if PROCESSED.exists() or SEALED.exists() or MANIFEST_PATH.exists():
        raise SystemExit("P5FC split state exists; refusing overwrite")
    source_audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
    if source_audit["status"] != "PASS":
        raise SystemExit("source audit has not passed")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    PROCESSED.mkdir(parents=True)
    SEALED.mkdir(parents=True)
    cipher_key = Fernet.generate_key()
    commitment_key = os.urandom(32)
    (SEALED / "test.key").write_bytes(cipher_key)
    (SEALED / "commitment.key").write_bytes(commitment_key)
    cipher = Fernet(cipher_key)
    datasets = []

    for dataset in config["datasets"]:
        print(f"[{dataset}] preparing canonical graph", flush=True)
        adjacency = load_graphsaint_adjacency(RAW / dataset / "adj_full.npz")
        edges = canonical_undirected_edges(adjacency)
        nodes = adjacency.shape[0]
        external_ids = tuple(str(index) for index in range(nodes))
        homes = balanced_sha256_homes(
            dataset,
            external_ids,
            clients=config["clients"],
            seed=config["home_assignment"]["seed"],
        )
        local = PROCESSED / dataset
        local.mkdir(parents=True)
        np.savez_compressed(local / "public_layout.npz", homes=homes)
        split_records = []
        for seed in config["split"]["seeds"]:
            print(f"[{dataset}] seed={seed}", flush=True)
            train_positive, validation_positive, test_positive = (
                capped_stratified_positive_split(
                    edges,
                    homes,
                    seed=seed,
                    validation_cap=config["split"]["validation_positive_cap"],
                    test_cap=config["split"]["test_positive_cap"],
                )
            )
            validation_negative, test_negative = sample_stratified_nonedges(
                edges,
                homes,
                seed=seed + 0x5F3759DF,
                validation_cap=config["split"]["validation_positive_cap"],
                test_cap=config["split"]["test_positive_cap"],
            )
            development_path = local / f"seed_{seed}_development.npz"
            np.savez_compressed(
                development_path,
                train_positive=train_positive,
                validation_positive=validation_positive,
                validation_negative=validation_negative,
            )
            token = encrypted_npz(
                cipher,
                test_positive=test_positive,
                test_negative=test_negative,
            )
            sealed_path = SEALED / f"{dataset}_seed_{seed}.fernet"
            sealed_path.write_bytes(token)
            split_records.append({
                "seed": seed,
                "counts": {
                    "train_positive": len(train_positive),
                    "validation_positive": len(validation_positive),
                    "validation_negative": len(validation_negative),
                    "test_positive": len(test_positive),
                    "test_negative": len(test_negative),
                    "validation_positive_strata": strata(validation_positive, homes),
                    "validation_negative_strata": strata(validation_negative, homes),
                    "test_positive_strata": strata(test_positive, homes),
                    "test_negative_strata": strata(test_negative, homes),
                },
                "commitments": {
                    "train_positive": array_commitment(
                        commitment_key,
                        f"{dataset}|{seed}|train",
                        train_positive,
                    ),
                    "validation_positive": array_commitment(
                        commitment_key,
                        f"{dataset}|{seed}|validation_positive",
                        validation_positive,
                    ),
                    "validation_negative": array_commitment(
                        commitment_key,
                        f"{dataset}|{seed}|validation_negative",
                        validation_negative,
                    ),
                    "test_positive": array_commitment(
                        commitment_key,
                        f"{dataset}|{seed}|test_positive",
                        test_positive,
                    ),
                    "test_negative": array_commitment(
                        commitment_key,
                        f"{dataset}|{seed}|test_negative",
                        test_negative,
                    ),
                    "sealed_payload_sha256": hashlib.sha256(token).hexdigest(),
                    "development_file_sha256": sha256(development_path),
                },
            })
        datasets.append({
            "dataset": dataset,
            "nodes": nodes,
            "canonical_undirected_edges": len(edges),
            "client_node_counts": np.bincount(
                homes, minlength=config["clients"]
            ).tolist(),
            "splits": split_records,
        })

    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": config["protocol"],
        "preparation_code_commit": git_head(),
        "config_sha256": sha256(CONFIG_PATH),
        "source_audit_sha256": sha256(SOURCE_AUDIT_PATH),
        "test_status": "encrypted_never_accessed",
        "test_access_count": 0,
        "test_identity_encryption": "operational accidental-access control",
        "contains_private_identities": False,
        "datasets": datasets,
    }
    MANIFEST_PATH.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(MANIFEST_PATH)


if __name__ == "__main__":
    main()
