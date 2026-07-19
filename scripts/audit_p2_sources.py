"""Audit P2 raw sources without emitting private rows or node identifiers."""

from __future__ import annotations

import csv
import json
import pathlib
import zipfile
from collections import Counter
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "manifests" / "p2_source_audit.json"


def canonical_edge(left: int, right: int) -> tuple[int, int]:
    return (left, right) if left < right else (right, left)


def audit_blogcatalog() -> dict:
    archive = RAW / "blogcatalog-v3" / "blogcatalog-v3.zip"
    with zipfile.ZipFile(archive) as handle:
        def rows(name: str):
            with handle.open(f"BlogCatalog-dataset/data/{name}") as stream:
                yield from csv.reader(line.decode("utf-8").strip() for line in stream)

        nodes = {int(row[0]) for row in rows("nodes.csv") if row}
        groups = {int(row[0]) for row in rows("groups.csv") if row}
        edge_rows = [(int(row[0]), int(row[1])) for row in rows("edges.csv") if row]
        memberships = [
            (int(row[0]), int(row[1])) for row in rows("group-edges.csv") if row
        ]

    self_loops = sum(left == right for left, right in edge_rows)
    canonical = {
        canonical_edge(left, right)
        for left, right in edge_rows
        if left != right
    }
    membership_nodes = {node for node, _ in memberships}
    membership_groups = {group for _, group in memberships}
    return {
        "dataset": "blogcatalog-v3",
        "raw_node_rows": len(nodes),
        "raw_edge_rows": len(edge_rows),
        "self_loop_rows": self_loops,
        "duplicate_or_reversed_edge_rows": len(edge_rows) - self_loops - len(canonical),
        "canonical_undirected_edges": len(canonical),
        "group_count": len(groups),
        "membership_rows": len(memberships),
        "nodes_without_membership": len(nodes - membership_nodes),
        "edge_endpoints_outside_node_dictionary": sum(
            left not in nodes or right not in nodes for left, right in edge_rows
        ),
        "membership_nodes_outside_dictionary": len(membership_nodes - nodes),
        "membership_groups_outside_dictionary": len(membership_groups - groups),
        "source_statistics_match": (
            len(nodes) == 10312
            and len(edge_rows) == 333983
            and len(canonical) == 333983
            and len(groups) == 39
        ),
    }


def audit_facebook() -> dict:
    directory = RAW / "facebook-musae"
    with (directory / "facebook_target.csv").open(
        newline="", encoding="utf-8", errors="replace"
    ) as handle:
        target_rows = list(csv.DictReader(handle))
    node_ids = {int(row["id"]) for row in target_rows}
    categories = Counter(row["page_type"] for row in target_rows)

    with (directory / "facebook_edges.csv").open(newline="", encoding="utf-8") as handle:
        edge_rows = [
            (int(row["id_1"]), int(row["id_2"])) for row in csv.DictReader(handle)
        ]
    self_loops = sum(left == right for left, right in edge_rows)
    canonical = {
        canonical_edge(left, right)
        for left, right in edge_rows
        if left != right
    }

    features = json.loads((directory / "facebook.json").read_text(encoding="utf-8"))
    feature_nodes = {int(node) for node in features}
    feature_indices = [index for values in features.values() for index in values]
    feature_dimension = max(feature_indices) + 1 if feature_indices else 0
    return {
        "dataset": "facebook-musae",
        "raw_node_rows": len(target_rows),
        "unique_node_ids": len(node_ids),
        "raw_edge_rows": len(edge_rows),
        "self_loop_rows": self_loops,
        "duplicate_or_reversed_edge_rows": len(edge_rows) - self_loops - len(canonical),
        "canonical_undirected_edges": len(canonical),
        "feature_nodes": len(feature_nodes),
        "feature_dimension": feature_dimension,
        "category_count": len(categories),
        "category_sizes": dict(sorted(categories.items())),
        "edge_endpoints_outside_target": sum(
            left not in node_ids or right not in node_ids for left, right in edge_rows
        ),
        "feature_nodes_outside_target": len(feature_nodes - node_ids),
        "target_nodes_without_features": len(node_ids - feature_nodes),
        "snap_reported_edge_rows": 171002,
        "snap_count_interpretation": (
            "matches raw repository rows"
            if len(edge_rows) == 171002
            else "does not match raw repository rows"
        ),
        "source_statistics_match": (
            len(target_rows) == 22470
            and len(node_ids) == 22470
            and len(edge_rows) == 171002
            and len(categories) == 4
        ),
    }


def main() -> None:
    datasets = [audit_blogcatalog(), audit_facebook()]
    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "privacy_note": "aggregate source audit; contains no edges or node identifiers",
        "datasets": datasets,
        "all_source_rows_match": all(item["source_statistics_match"] for item in datasets),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_source_rows_match"]:
        raise SystemExit("source audit failed: see aggregate mismatch fields")


if __name__ == "__main__":
    main()
