"""Aggregate integrity audit for untouched P2.1 confirmatory sources."""

from __future__ import annotations

import csv
import io
import json
import pathlib
import zipfile
from collections import Counter
from datetime import datetime, timezone

import networkx as nx


ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "manifests" / "p2_1_source_audit.json"


def canonical(left: int, right: int) -> tuple[int, int]:
    return (left, right) if left < right else (right, left)


def audit_polblogs() -> dict:
    archive = RAW / "polblogs-newman" / "polblogs-newman.zip"
    with zipfile.ZipFile(archive) as handle:
        content = handle.read("polblogs.gml").decode("ascii")
    multigraph_content = content.replace("graph [", "graph [\n  multigraph 1", 1)
    graph = nx.parse_gml(multigraph_content.splitlines(), label="id")
    raw_directed_edges = [(int(left), int(right)) for left, right in graph.edges()]
    directed_edges = set(raw_directed_edges)
    loops = sum(left == right for left, right in directed_edges)
    undirected = {
        canonical(left, right) for left, right in directed_edges if left != right
    }
    labels = Counter(int(attributes["value"]) for _, attributes in graph.nodes(data=True))
    return {
        "dataset": "polblogs-newman",
        "nodes": graph.number_of_nodes(),
        "raw_directed_edge_blocks": len(raw_directed_edges),
        "duplicate_directed_edge_blocks": len(raw_directed_edges) - len(directed_edges),
        "unique_directed_links": len(directed_edges),
        "self_loop_rows": loops,
        "canonical_simple_undirected_edges": len(undirected),
        "reciprocal_collapse_count": len(directed_edges) - loops - len(undirected),
        "public_label_count": len(labels),
        "public_label_sizes": {str(key): value for key, value in sorted(labels.items())},
        "source_statistics_match": (
            graph.number_of_nodes() == 1490
            and len(directed_edges) == 19025
            and len(labels) == 2
        ),
    }


def audit_lastfm() -> dict:
    archive = RAW / "lastfm-asia-snap" / "lastfm-asia-snap.zip"
    with zipfile.ZipFile(archive) as handle:
        def dictionary_rows(name: str):
            text = io.TextIOWrapper(handle.open(f"lasftm_asia/{name}"), encoding="utf-8")
            try:
                yield from csv.DictReader(text)
            finally:
                text.detach()

        targets = list(dictionary_rows("lastfm_asia_target.csv"))
        edges = [
            (int(row["node_1"]), int(row["node_2"]))
            for row in dictionary_rows("lastfm_asia_edges.csv")
        ]
        features = json.loads(handle.read("lasftm_asia/lastfm_asia_features.json"))
    node_ids = {int(row["id"]) for row in targets}
    labels = Counter(int(row["target"]) for row in targets)
    loops = sum(left == right for left, right in edges)
    undirected = {canonical(left, right) for left, right in edges if left != right}
    feature_nodes = {int(node) for node in features}
    indices = [index for values in features.values() for index in values]
    return {
        "dataset": "lastfm-asia-snap",
        "raw_node_rows": len(targets),
        "unique_node_ids": len(node_ids),
        "raw_edge_rows": len(edges),
        "self_loop_rows": loops,
        "duplicate_or_reversed_edge_rows": len(edges) - loops - len(undirected),
        "canonical_simple_undirected_edges": len(undirected),
        "feature_nodes": len(feature_nodes),
        "feature_dimension": max(indices) + 1 if indices else 0,
        "public_label_count": len(labels),
        "edge_endpoints_outside_target": sum(
            left not in node_ids or right not in node_ids for left, right in edges
        ),
        "feature_nodes_outside_target": len(feature_nodes - node_ids),
        "target_nodes_without_features": len(node_ids - feature_nodes),
        "source_statistics_match": (
            len(targets) == 7624
            and len(node_ids) == 7624
            and len(edges) == 27806
            and len(undirected) == 27806
        ),
    }


def main() -> None:
    datasets = [audit_polblogs(), audit_lastfm()]
    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "privacy_note": "aggregate audit without node identities or edges",
        "datasets": datasets,
        "all_source_rows_match": all(item["source_statistics_match"] for item in datasets),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_source_rows_match"]:
        raise SystemExit("P2.1 source audit failed")


if __name__ == "__main__":
    main()
