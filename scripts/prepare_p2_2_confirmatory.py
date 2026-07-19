"""Prepare P2.2 operational validation data and encrypted one-time tests."""

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
    balanced_sha256_homes,
    load_deezer_europe,
    load_github_social,
    public_coarsening,
    stratified_link_split,
)
from fed_dp_lp.p2_sealing import array_commitment, encrypted_npz


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_2_confirmatory.json"
SOURCE_AUDIT = ROOT / "data" / "manifests" / "p2_2_source_audit.json"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "p2_2_confirmatory"
SEALED = ROOT / "data" / "sealed" / "p2_2_confirmatory"
OUTPUT = ROOT / "data" / "manifests" / "p2_2_split_manifest.json"
PROTOCOL_COMMIT = "08fa3e37838933092cc0cf6f318eef109cbd3386"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def load_graph(dataset: str):
    archive = RAW / dataset / f"{dataset}.zip"
    if dataset == "github-social-snap":
        return load_github_social(archive)
    if dataset == "deezer-europe-snap":
        return load_deezer_europe(archive)
    raise ValueError(dataset)


def stratum_counts(pairs: np.ndarray, homes: np.ndarray) -> dict[str, int]:
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    return {"intra": int(np.sum(~cross)), "cross": int(np.sum(cross))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initialize-sealed-confirmatory", action="store_true")
    args = parser.parse_args()
    if not args.initialize_sealed_confirmatory:
        raise SystemExit("refusing P2.2 split preparation without explicit initialization")
    if OUTPUT.exists() or PROCESSED.exists() or SEALED.exists():
        raise SystemExit("P2.2 split state exists; refusing overwrite")
    source_audit = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))
    if not source_audit["all_sources_pass"]:
        raise SystemExit("refusing split preparation after failed source audit")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    PROCESSED.mkdir(parents=True)
    SEALED.mkdir(parents=True)
    cipher_key = Fernet.generate_key()
    commitment_key = os.urandom(32)
    (SEALED / "test.key").write_bytes(cipher_key)
    (SEALED / "commitment.key").write_bytes(commitment_key)
    cipher = Fernet(cipher_key)
    datasets = []

    for dataset in config["datasets"]:
        graph = load_graph(dataset)
        homes = balanced_sha256_homes(
            dataset,
            graph.external_ids,
            clients=config["clients"],
            seed=config["home_assignment"]["seed"],
        )
        coarsening = config["public_coarsening"]
        cells = public_coarsening(
            graph.public_features,
            cells=coarsening["cells"],
            components=coarsening["components"],
            random_state=coarsening["random_state"],
        )
        local = PROCESSED / dataset
        local.mkdir(parents=True)
        np.savez_compressed(local / "public_layout.npz", homes=homes, cells=cells)
        (local / "external_ids.json").write_text(
            json.dumps(graph.external_ids) + "\n", encoding="utf-8"
        )
        split_records = []
        for seed in config["split"]["seeds"]:
            split = stratified_link_split(graph.edges, homes, seed=seed)
            np.savez_compressed(
                local / f"seed_{seed}_development.npz",
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
            sealed = SEALED / f"{dataset}_seed_{seed}.fernet"
            sealed.write_bytes(token)
            split_records.append(
                {
                    "seed": seed,
                    "counts": {
                        "train_positive": len(split.train_positive),
                        "validation_positive": len(split.validation_positive),
                        "test_positive": len(split.test_positive),
                        "test_negative": len(split.test_negative),
                        "test_positive_strata": stratum_counts(
                            split.test_positive, homes
                        ),
                        "test_negative_strata": stratum_counts(
                            split.test_negative, homes
                        ),
                    },
                    "commitments": {
                        "train_positive": array_commitment(
                            commitment_key,
                            f"{dataset}|{seed}|train",
                            split.train_positive,
                        ),
                        "validation_positive": array_commitment(
                            commitment_key,
                            f"{dataset}|{seed}|validation",
                            split.validation_positive,
                        ),
                        "test_positive": array_commitment(
                            commitment_key,
                            f"{dataset}|{seed}|test_positive",
                            split.test_positive,
                        ),
                        "test_negative": array_commitment(
                            commitment_key,
                            f"{dataset}|{seed}|test_negative",
                            split.test_negative,
                        ),
                        "sealed_payload_sha256": hashlib.sha256(token).hexdigest(),
                    },
                }
            )
        owners = homes[graph.edges[:, 0]]
        datasets.append(
            {
                "dataset": dataset,
                "nodes": len(graph.external_ids),
                "canonical_edges": len(graph.edges),
                "public_feature_dimension": graph.public_features.shape[1],
                "public_feature_nnz": int(graph.public_features.nnz),
                "empty_public_feature_nodes": int(
                    np.sum(np.diff(graph.public_features.indptr) == 0)
                ),
                "client_node_counts": np.bincount(
                    homes, minlength=config["clients"]
                ).tolist(),
                "client_owned_edge_counts": np.bincount(
                    owners, minlength=config["clients"]
                ).tolist(),
                "public_cell_counts": np.bincount(
                    cells, minlength=coarsening["cells"]
                ).tolist(),
                "splits": split_records,
            }
        )

    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "confirmatory_protocol_commit": PROTOCOL_COMMIT,
        "preparation_code_commit": git_head(),
        "config_sha256": sha256(CONFIG),
        "source_audit_sha256": sha256(SOURCE_AUDIT),
        "test_status": "encrypted_never_accessed",
        "test_access_count": 0,
        "contains_private_identities": False,
        "datasets": datasets,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
