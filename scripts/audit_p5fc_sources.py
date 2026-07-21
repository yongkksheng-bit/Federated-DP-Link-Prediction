"""Audit P5FC source bytes before split generation."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np

from fed_dp_lp.p5fc_data import (
    canonical_undirected_edges,
    feature_matrix_audit,
    load_graphsaint_adjacency,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data/p5fc_source_registry.json"
MANIFEST_PATH = ROOT / "data/manifests/p5fc_sources.json"
RAW = ROOT / "data/raw/p5fc"
OUTPUT = ROOT / "data/manifests/p5fc_source_audit.json"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    registered = {dataset["id"]: dataset for dataset in registry["datasets"]}
    manifested = {
        (item["dataset"], item["path"]): item for item in manifest["files"]
    }
    expected_keys = {
        (dataset["id"], item["path"])
        for dataset in registry["datasets"] for item in dataset["files"]
    }
    dataset_audits = []
    hashes_current = True
    for dataset_id, expected in registered.items():
        directory = RAW / dataset_id
        adjacency_path = directory / "adj_full.npz"
        feature_path = directory / "feats.npy"
        for path in (adjacency_path, feature_path):
            item = manifested[(dataset_id, path.name)]
            hashes_current = hashes_current and item["sha256"] == sha256(path)

        adjacency = load_graphsaint_adjacency(adjacency_path)
        diagonal_nonzero = int(np.count_nonzero(adjacency.diagonal()))
        asymmetry_nnz = int((adjacency != adjacency.T).nnz)
        edges = canonical_undirected_edges(adjacency)
        feature_audit = feature_matrix_audit(feature_path)
        dataset_audits.append({
            "dataset": dataset_id,
            "adjacency_shape": [int(value) for value in adjacency.shape],
            "adjacency_nnz": int(adjacency.nnz),
            "adjacency_dtype": str(adjacency.dtype),
            "self_loop_count": diagonal_nonzero,
            "asymmetry_nnz": asymmetry_nnz,
            "canonical_undirected_edges": int(len(edges)),
            "features": feature_audit,
            "checks": {
                "node_count": adjacency.shape
                == (expected["expected_nodes"], expected["expected_nodes"]),
                "adjacency_nnz": adjacency.nnz
                == expected["expected_adjacency_nnz"],
                "symmetric": asymmetry_nnz == 0,
                "no_self_loops": diagonal_nonzero == 0,
                "feature_shape": feature_audit["shape"]
                == [expected["expected_nodes"], expected["expected_feature_columns"]],
                "features_finite": feature_audit["all_finite"],
            },
        })

    prohibited_names = {"class_map.json", "role.json", "data.pt"}
    prohibited_present = sorted(
        str(path.relative_to(ROOT)) for path in RAW.rglob("*")
        if path.is_file() and path.name in prohibited_names
    )
    checks = {
        "registry_hash_current": manifest["registry_sha256"] == sha256(REGISTRY_PATH),
        "manifest_exact_allowlist": set(manifested) == expected_keys,
        "manifest_denies_labels_and_roles": not manifest[
            "labels_or_source_roles_acquired"
        ],
        "source_hashes_current": hashes_current,
        "no_prohibited_files": not prohibited_present,
        "dataset_integrity": all(
            all(item["checks"].values()) for item in dataset_audits
        ),
    }
    audit = {
        "schema_version": 1,
        "protocol": "P5FC_SOURCE_INTEGRITY_AUDIT_v1",
        "checks": checks,
        "datasets": dataset_audits,
        "prohibited_files_present": prohibited_present,
        "status": "PASS" if all(checks.values()) else "STOP",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
