"""Prepare edge-independent P2 inputs and encrypted, untouched test payloads."""

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

from fed_dp_lp.p2_data import (
    PilotGraph,
    balanced_sha256_homes,
    load_blogcatalog,
    load_facebook,
    public_coarsening,
    stratified_link_split,
)
from fed_dp_lp.p2_sealing import array_commitment, encrypted_npz


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_pilot.json"
SOURCE_MANIFEST = ROOT / "data" / "manifests" / "p2_sources.json"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "p2_pilot"
SEALED = ROOT / "data" / "sealed" / "p2_pilot"
OUTPUT = ROOT / "data" / "manifests" / "p2_split_manifest.json"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stratum_counts(pairs: np.ndarray, homes: np.ndarray) -> dict[str, int]:
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    return {"intra": int((~cross).sum()), "cross": int(cross.sum())}


def load_graph(dataset_id: str) -> PilotGraph:
    if dataset_id == "blogcatalog-v3":
        return load_blogcatalog(RAW / dataset_id / "blogcatalog-v3.zip")
    if dataset_id == "facebook-musae":
        return load_facebook(RAW / dataset_id)
    raise ValueError(f"dataset is not P2-allowlisted: {dataset_id}")


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--initialize-sealed-pilot",
        action="store_true",
        help="Confirm one-time creation of the frozen P2 split payloads.",
    )
    args = parser.parse_args()
    if not args.initialize_sealed_pilot:
        raise SystemExit("refusing to prepare real splits without explicit initialization")
    if OUTPUT.exists():
        raise SystemExit("split manifest already exists; refusing to overwrite frozen splits")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    PROCESSED.mkdir(parents=True, exist_ok=True)
    SEALED.mkdir(parents=True, exist_ok=True)

    fernet_key = Fernet.generate_key()
    commitment_key = os.urandom(32)
    (SEALED / "test.key").write_bytes(fernet_key)
    (SEALED / "commitment.key").write_bytes(commitment_key)
    cipher = Fernet(fernet_key)
    dataset_records: list[dict] = []

    for dataset_id in config["datasets"]:
        graph = load_graph(dataset_id)
        homes = balanced_sha256_homes(
            dataset_id,
            graph.external_ids,
            clients=config["clients"],
            seed=config["home_assignment"]["seed"],
        )
        cells = public_coarsening(
            graph.public_features,
            cells=config["public_coarsening"]["cells"],
            components=config["public_coarsening"]["components"],
            random_state=config["public_coarsening"]["random_state"],
        )
        dataset_directory = PROCESSED / dataset_id
        dataset_directory.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(dataset_directory / "public_layout.npz", homes=homes, cells=cells)
        (dataset_directory / "external_ids.json").write_text(
            json.dumps(graph.external_ids) + "\n", encoding="utf-8"
        )

        split_records: list[dict] = []
        for seed in config["split"]["seeds"]:
            split = stratified_link_split(graph.edges, homes, seed=seed)
            np.savez_compressed(
                dataset_directory / f"seed_{seed}_development.npz",
                train_positive=split.train_positive,
                train_negative=split.train_negative,
                validation_positive=split.validation_positive,
                validation_negative=split.validation_negative,
            )
            token = encrypted_npz(
                cipher,
                test_positive=split.test_positive,
                test_negative=split.test_negative,
            )
            sealed_path = SEALED / f"{dataset_id}_seed_{seed}.fernet"
            sealed_path.write_bytes(token)
            split_records.append(
                {
                    "seed": seed,
                    "counts": {
                        "train_positive": len(split.train_positive),
                        "validation_positive": len(split.validation_positive),
                        "test_positive": len(split.test_positive),
                        "test_negative": len(split.test_negative),
                        "test_positive_strata": stratum_counts(split.test_positive, homes),
                        "test_negative_strata": stratum_counts(split.test_negative, homes),
                    },
                    "commitments": {
                        "train_positive": array_commitment(
                            commitment_key, f"{dataset_id}|{seed}|train_positive", split.train_positive
                        ),
                        "validation_positive": array_commitment(
                            commitment_key,
                            f"{dataset_id}|{seed}|validation_positive",
                            split.validation_positive,
                        ),
                        "test_positive": array_commitment(
                            commitment_key, f"{dataset_id}|{seed}|test_positive", split.test_positive
                        ),
                        "test_negative": array_commitment(
                            commitment_key, f"{dataset_id}|{seed}|test_negative", split.test_negative
                        ),
                        "sealed_payload_sha256": hashlib.sha256(token).hexdigest(),
                    },
                }
            )

        owners = homes[graph.edges[:, 0]]
        dataset_records.append(
            {
                "dataset": dataset_id,
                "nodes": len(graph.external_ids),
                "canonical_edges": len(graph.edges),
                "public_feature_dimension": graph.public_features.shape[1],
                "client_node_counts": np.bincount(
                    homes, minlength=config["clients"]
                ).tolist(),
                "client_owned_edge_counts": np.bincount(
                    owners, minlength=config["clients"]
                ).tolist(),
                "public_cell_counts": np.bincount(
                    cells, minlength=config["public_coarsening"]["cells"]
                ).tolist(),
                "splits": split_records,
            }
        )

    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_commit": "990df5845163e82cfc99fd3853819fa3f1a5f08e",
        "preparation_code_commit": git_head(),
        "config_sha256": sha256(CONFIG),
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "source_registry_sha256": source_manifest["registry_sha256"],
        "test_status": "encrypted_never_accessed",
        "test_access_count": 0,
        "contains_private_identities": false,
        "datasets": dataset_records,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote frozen aggregate split manifest: {OUTPUT}")


if __name__ == "__main__":
    main()
