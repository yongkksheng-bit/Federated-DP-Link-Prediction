"""Audit registered P2.2 source bytes and aggregate parser invariants."""

from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import zipfile

import numpy as np

from fed_dp_lp.p2_data import load_deezer_europe, load_github_social


ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "p2_2_source_registry.json"
OUTPUT = ROOT / "data" / "manifests" / "p2_2_source_audit.json"


SPECS = {
    "github-social-snap": {
        "path": ROOT / "data" / "raw" / "github-social-snap" / "github-social-snap.zip",
        "loader": load_github_social,
        "prefix": "git_web_ml/",
        "edge": "musae_git_edges.csv",
        "features": "musae_git_features.json",
        "target": "musae_git_target.csv",
        "edge_columns": ("id_1", "id_2"),
    },
    "deezer-europe-snap": {
        "path": ROOT / "data" / "raw" / "deezer-europe-snap" / "deezer-europe-snap.zip",
        "loader": load_deezer_europe,
        "prefix": "deezer_europe/",
        "edge": "deezer_europe_edges.csv",
        "features": "deezer_europe_features.json",
        "target": "deezer_europe_target.csv",
        "edge_columns": ("node_1", "node_2"),
    },
}


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(dataset: str, expected: dict) -> dict:
    spec = SPECS[dataset]
    graph = spec["loader"](spec["path"])
    with zipfile.ZipFile(spec["path"]) as handle:
        members = sorted(handle.namelist())
        with handle.open(spec["prefix"] + spec["edge"]) as stream:
            edge_rows = list(
                csv.DictReader(line.decode("utf-8").strip() for line in stream)
            )
        with handle.open(spec["prefix"] + spec["target"]) as stream:
            targets = list(
                csv.DictReader(line.decode("utf-8").strip() for line in stream)
            )
        features = json.loads(
            handle.read(spec["prefix"] + spec["features"]).decode("utf-8")
        )
    left_name, right_name = spec["edge_columns"]
    raw_pairs = [(row[left_name], row[right_name]) for row in edge_rows]
    self_loops = sum(left == right for left, right in raw_pairs)
    canonical = [(min(int(left), int(right)), max(int(left), int(right))) for left, right in raw_pairs if left != right]
    unique = set(canonical)
    feature_nnz = sum(len(values) for values in features.values())
    feature_dimension = max(
        (index for values in features.values() for index in values), default=-1
    ) + 1
    empty_feature_nodes = sum(not values for values in features.values())
    result = {
        "dataset": dataset,
        "archive_sha256": digest(spec["path"]),
        "archive_bytes": spec["path"].stat().st_size,
        "archive_members": members,
        "raw_edge_rows": len(raw_pairs),
        "raw_self_loops": self_loops,
        "raw_duplicate_canonical_rows": len(canonical) - len(unique),
        "canonical_undirected_edges": len(graph.edges),
        "target_nodes": len(targets),
        "feature_nodes": len(features),
        "feature_dimension": feature_dimension,
        "feature_nnz": feature_nnz,
        "empty_feature_nodes": empty_feature_nodes,
        "parser_nodes": len(graph.external_ids),
        "parser_feature_shape": list(graph.public_features.shape),
        "parser_feature_nnz": int(graph.public_features.nnz),
        "canonical_edges_strict": bool(np.all(graph.edges[:, 0] < graph.edges[:, 1])),
        "expected_nodes_match": len(graph.external_ids) == expected["expected_nodes"],
        "expected_edges_match": len(graph.edges) == expected["expected_undirected_edges"],
        "node_universes_match": set(features) == {row["id"] for row in targets},
    }
    result["pass"] = all(
        result[key]
        for key in (
            "canonical_edges_strict",
            "expected_nodes_match",
            "expected_edges_match",
            "node_universes_match",
        )
    )
    return result


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("P2.2 source audit already exists; refusing overwrite")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    records = [audit(item["dataset"], item) for item in registry["sources"]]
    payload = {
        "schema_version": 1,
        "registry_sha256": digest(REGISTRY),
        "all_sources_pass": all(record["pass"] for record in records),
        "datasets": records,
        "privacy_note": "aggregate source audit; contains no edges or node identifiers",
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()
