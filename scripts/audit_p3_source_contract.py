"""Snapshot six P3 source byte identities and target-excluding public views."""

from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np

from fed_dp_lp.p3_data import load_p3_graph


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p3_master_benchmark.json"
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "manifests" / "p3_source_contract.json"


SOURCE_FILES = {
    "blogcatalog-v3": ["blogcatalog-v3/blogcatalog-v3.zip"],
    "facebook-musae": [
        "facebook-musae/facebook_edges.csv",
        "facebook-musae/facebook.json",
        "facebook-musae/facebook_target.csv",
    ],
    "polblogs-newman": ["polblogs-newman/polblogs-newman.zip"],
    "lastfm-asia-snap": ["lastfm-asia-snap/lastfm-asia-snap.zip"],
    "github-social-snap": ["github-social-snap/github-social-snap.zip"],
    "deezer-europe-snap": ["deezer-europe-snap/deezer-europe-snap.zip"],
}


EXPECTED = {
    "blogcatalog-v3": (10312, 333983),
    "facebook-musae": (22470, 170823),
    "polblogs-newman": (1490, 16715),
    "lastfm-asia-snap": (7624, 27806),
    "github-social-snap": (37700, 289003),
    "deezer-europe-snap": (28281, 92752),
}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("P3 source contract already exists; refusing overwrite")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    records = []
    for dataset in config["datasets"]:
        graph = load_p3_graph(RAW, dataset)
        expected_nodes, expected_edges = EXPECTED[dataset]
        files = [RAW / relative for relative in SOURCE_FILES[dataset]]
        record = {
            "dataset": dataset,
            "source_files": [
                {
                    "relative_path": str(path.relative_to(RAW)).replace("\\", "/"),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
                for path in files
            ],
            "nodes": len(graph.external_ids),
            "canonical_undirected_edges": len(graph.edges),
            "public_feature_dimension": graph.public_features.shape[1],
            "public_feature_nnz": int(graph.public_features.nnz),
            "empty_public_feature_nodes": int(
                np.sum(np.diff(graph.public_features.indptr) == 0)
            ),
            "canonical_edges_strict": bool(
                np.all(graph.edges[:, 0] < graph.edges[:, 1])
            ),
            "expected_nodes_match": len(graph.external_ids) == expected_nodes,
            "expected_edges_match": len(graph.edges) == expected_edges,
            "classification_target_excluded": dataset
            in {
                "facebook-musae",
                "lastfm-asia-snap",
                "github-social-snap",
                "deezer-europe-snap",
            },
        }
        record["pass"] = all(
            record[key]
            for key in (
                "canonical_edges_strict",
                "expected_nodes_match",
                "expected_edges_match",
            )
        )
        records.append(record)
    payload = {
        "schema_version": 1,
        "config_sha256": sha256(CONFIG),
        "all_sources_pass": all(record["pass"] for record in records),
        "datasets": records,
        "contains_private_identities": False,
        "note": "aggregate source and public-view audit only",
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()
