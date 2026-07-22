"""Compute the frozen training-only P6A dataset property matrix."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

import numpy as np

from fed_dp_lp.dataset_properties import (
    common_neighbor_scores,
    public_descriptor_properties,
    topology_properties,
)
from fed_dp_lp.metrics import roc_auc
from fed_dp_lp.p2_pilot import candidate_arrays, sparse_cosine_scores
from fed_dp_lp.p3_data import load_p3_graph


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p6a_dataset_property_matrix.json"
MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p3_split_audit.json"
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed/p3_benchmark"
OUTPUT = ROOT / "results/p6a_dataset_property_matrix"


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


def write_jsonl(path: pathlib.Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def aggregate(records: list[dict], properties: list[str]) -> dict:
    datasets: dict[str, dict] = {}
    for dataset in sorted({record["dataset"] for record in records}):
        subset = [record for record in records if record["dataset"] == dataset]
        datasets[dataset] = {
            "seeds": len(subset),
            "properties": {
                name: {
                    "mean": float(np.mean([row["properties"][name] for row in subset])),
                    "sample_std": float(np.std(
                        [row["properties"][name] for row in subset], ddof=1
                    )),
                }
                for name in properties
            },
        }
    return datasets


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("P6A output exists; refusing overwrite")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("P3 split audit is not clean")
    if config["development_datasets"] != master["datasets"]:
        raise SystemExit("P6A domains differ from frozen P3 development domains")
    if config["development_seeds"] != master["split"]["seeds"]:
        raise SystemExit("P6A seeds differ from frozen P3 seeds")

    diagnostics = config["graph_diagnostics"]
    commit = git_head()
    records: list[dict] = []
    for dataset in config["development_datasets"]:
        print(f"[{dataset}] loading public source", flush=True)
        graph = load_p3_graph(RAW, dataset)
        descriptor_properties = public_descriptor_properties(graph.public_features)
        layout_path = PROCESSED / dataset / "public_layout.npz"
        with np.load(layout_path, allow_pickle=False) as source:
            homes = source["homes"]
        for seed in config["development_seeds"]:
            development_path = PROCESSED / dataset / f"seed_{seed}_development.npz"
            with np.load(development_path, allow_pickle=False) as source:
                train_positive = source["train_positive"]
                validation_positive = source["validation_positive"]
                validation_negative = source["validation_negative"]
            topology, adjacency = topology_properties(
                len(graph.external_ids),
                train_positive,
                homes,
                clustering_node_cap=diagnostics["clustering_node_cap"],
                clustering_seed=seed + diagnostics["clustering_seed_offset"],
                louvain_resolution=diagnostics["louvain_resolution"],
                louvain_seed=seed + diagnostics["louvain_seed_offset"],
            )
            pairs, labels = candidate_arrays(validation_positive, validation_negative)
            public_scores = sparse_cosine_scores(graph.public_features, pairs)
            common_neighbor = common_neighbor_scores(adjacency, pairs)
            degrees = np.asarray(adjacency.sum(axis=1)).ravel()
            preferential_attachment = degrees[pairs[:, 0]] * degrees[pairs[:, 1]]
            properties = {
                "public_feature_auc": roc_auc(labels, public_scores),
                "common_neighbor_auc": roc_auc(labels, common_neighbor),
                "preferential_attachment_auc": roc_auc(labels, preferential_attachment),
                **topology,
                **descriptor_properties,
            }
            if not all(np.isfinite(value) for value in properties.values()):
                raise RuntimeError(f"non-finite property for {dataset} seed {seed}")
            records.append({
                "protocol": config["protocol"],
                "code_commit": commit,
                "dataset": dataset,
                "seed": seed,
                "split": "p3_training_topology_and_validation_candidates",
                "test_accessed": False,
                "config_sha256": sha256(CONFIG_PATH),
                "master_config_sha256": sha256(MASTER_PATH),
                "split_audit_sha256": sha256(SPLIT_AUDIT_PATH),
                "development_file_sha256": sha256(development_path),
                "public_layout_sha256": sha256(layout_path),
                "nodes": len(graph.external_ids),
                "train_positive_count": len(train_positive),
                "validation_positive_count": len(validation_positive),
                "validation_negative_count": len(validation_negative),
                "properties": properties,
            })
            print(f"[{dataset}] seed={seed} complete", flush=True)

    property_names = list(config["properties"])
    summary = {
        "protocol": config["protocol"],
        "record_count": len(records),
        "dataset_count": len(config["development_datasets"]),
        "seeds_per_dataset": len(config["development_seeds"]),
        "test_accessed": False,
        "datasets": aggregate(records, property_names),
    }
    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "records.jsonl", records)
    (OUTPUT / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "records": len(records),
        "datasets": len(summary["datasets"]),
        "test_accessed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
