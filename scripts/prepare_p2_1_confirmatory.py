"""Prepare P2.1 development inputs and newly encrypted confirmatory tests."""

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
    label_hash_subcells,
    load_lastfm,
    load_polblogs,
    public_coarsening,
    stratified_link_split,
)
from fed_dp_lp.p2_sealing import array_commitment, encrypted_npz


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_1_confirmatory.json"
SOURCE_MANIFEST = ROOT / "data" / "manifests" / "p2_1_sources.json"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "p2_1_confirmatory"
SEALED = ROOT / "data" / "sealed" / "p2_1_confirmatory"
OUTPUT = ROOT / "data" / "manifests" / "p2_1_split_manifest.json"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_graph(dataset: str):
    archive = RAW / dataset / f"{dataset}.zip"
    if dataset == "polblogs-newman":
        return load_polblogs(archive)
    if dataset == "lastfm-asia-snap":
        return load_lastfm(archive)
    raise ValueError(dataset)


def counts(pairs: np.ndarray, homes: np.ndarray) -> dict[str, int]:
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    return {"intra": int((~cross).sum()), "cross": int(cross.sum())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initialize-sealed-confirmatory", action="store_true")
    args = parser.parse_args()
    if not args.initialize_sealed_confirmatory:
        raise SystemExit("refusing P2.1 split preparation without explicit initialization")
    if OUTPUT.exists():
        raise SystemExit("P2.1 split manifest exists; refusing overwrite")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    PROCESSED.mkdir(parents=True, exist_ok=True)
    SEALED.mkdir(parents=True, exist_ok=True)
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
        coarsening = config["public_coarsening"][dataset]
        if dataset == "polblogs-newman":
            cells = label_hash_subcells(
                dataset,
                graph.external_ids,
                graph.public_labels,
                subcells_per_label=coarsening["subcells_per_label"],
                seed=config["home_assignment"]["seed"],
            )
        else:
            cells = public_coarsening(
                graph.public_features,
                cells=coarsening["cells"],
                components=coarsening["components"],
                random_state=coarsening["random_state"],
            )
        local = PROCESSED / dataset
        local.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(local / "public_layout.npz", homes=homes, cells=cells)
        (local / "external_ids.json").write_text(json.dumps(graph.external_ids) + "\n")
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
                        "test_positive_strata": counts(split.test_positive, homes),
                        "test_negative_strata": counts(split.test_negative, homes),
                    },
                    "commitments": {
                        "train_positive": array_commitment(
                            commitment_key, f"{dataset}|{seed}|train", split.train_positive
                        ),
                        "validation_positive": array_commitment(
                            commitment_key, f"{dataset}|{seed}|validation", split.validation_positive
                        ),
                        "test_positive": array_commitment(
                            commitment_key, f"{dataset}|{seed}|test_positive", split.test_positive
                        ),
                        "test_negative": array_commitment(
                            commitment_key, f"{dataset}|{seed}|test_negative", split.test_negative
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
                "client_node_counts": np.bincount(homes, minlength=config["clients"]).tolist(),
                "client_owned_edge_counts": np.bincount(
                    owners, minlength=config["clients"]
                ).tolist(),
                "public_cell_counts": np.bincount(cells, minlength=16).tolist(),
                "splits": split_records,
            }
        )

    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "confirmatory_protocol_commit": "178d52bb9b52ac20f51f6c7817d9700a75ddff50",
        "preparation_code_commit": git_head(),
        "config_sha256": sha256(CONFIG),
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "test_status": "encrypted_never_accessed",
        "test_access_count": 0,
        "contains_private_identities": False,
        "datasets": datasets,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
