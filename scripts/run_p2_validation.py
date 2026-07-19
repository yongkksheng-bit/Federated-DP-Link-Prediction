"""Run the frozen P2 pilot on development/validation inputs only."""

from __future__ import annotations

import json
import pathlib
import subprocess
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.block_release import (
    block_counts,
    make_block_layout,
    release_block_densities,
    score_pairs,
)
from fed_dp_lp.metrics import paired_summary
from fed_dp_lp.p2_data import load_blogcatalog, load_facebook
from fed_dp_lp.p2_pilot import (
    candidate_arrays,
    evaluate_scores,
    metric_masks,
    sparse_cosine_scores,
)
from fed_dp_lp.public_views import repartition_edges


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_pilot.json"
GATE = ROOT / "configs" / "p2_validation_gate.json"
MANIFEST = ROOT / "data" / "manifests" / "p2_split_manifest.json"
PROCESSED = ROOT / "data" / "processed" / "p2_pilot"
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "results" / "p2_validation"


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def sha256(path: pathlib.Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_graph(dataset: str):
    if dataset == "blogcatalog-v3":
        return load_blogcatalog(RAW / dataset / "blogcatalog-v3.zip")
    if dataset == "facebook-musae":
        return load_facebook(RAW / dataset)
    raise ValueError(dataset)


def run_record(dataset: str, seed: int, calibration, commit: str) -> dict:
    graph = load_graph(dataset)
    with np.load(PROCESSED / dataset / "public_layout.npz", allow_pickle=False) as layout_file:
        homes = layout_file["homes"]
        cells = layout_file["cells"]
    with np.load(
        PROCESSED / dataset / f"seed_{seed}_development.npz", allow_pickle=False
    ) as development:
        train_positive = development["train_positive"]
        validation_positive = development["validation_positive"]
        validation_negative = development["validation_negative"]

    pairs, labels = candidate_arrays(validation_positive, validation_negative)
    masks = metric_masks(pairs, homes)
    client_edges = repartition_edges(train_positive, homes, clients=5)
    empty_clients = tuple(np.empty((0, 2), dtype=np.int64) for _ in client_edges)
    block_layout = make_block_layout(cells)
    counts = sum(
        (block_counts(edges, cells, block_layout) for edges in client_edges),
        start=np.zeros(block_layout.dimension),
    )
    nonprivate_densities = counts / block_layout.capacities

    scores = {
        "public_cosine": sparse_cosine_scores(graph.public_features, pairs),
        "public_same_cell": (cells[pairs[:, 0]] == cells[pairs[:, 1]]).astype(float),
        "nonprivate_coarsened_oracle": score_pairs(
            pairs, cells, nonprivate_densities, block_layout
        ),
    }
    random_rng = np.random.default_rng(np.random.SeedSequence([seed, 701]))
    scores["random_score"] = random_rng.random(len(pairs))
    for name, edges, visibility, stream in (
        ("zero_private_signal", empty_clients, "visible_messages", 801),
        ("dp_coarsened_affinity_visible_messages", client_edges, "visible_messages", 901),
        ("dp_coarsened_affinity_ideal_secagg", client_edges, "ideal_secagg", 1001),
    ):
        rng = np.random.default_rng(np.random.SeedSequence([seed, stream]))
        _, densities, released_layout = release_block_densities(
            edges,
            cells,
            noise_std=calibration.noise_std,
            visibility=visibility,
            rng=rng,
        )
        scores[name] = score_pairs(pairs, cells, densities, released_layout)

    return {
        "protocol": "P2_VALIDATION_v1",
        "code_commit": commit,
        "dataset": dataset,
        "seed": seed,
        "split": "validation",
        "test_accessed": False,
        "config_sha256": sha256(CONFIG),
        "gate_sha256": sha256(GATE),
        "split_manifest_sha256": sha256(MANIFEST),
        "privacy": asdict(calibration),
        "release_dimension": block_layout.dimension,
        "l2_sensitivity": 1.0,
        "client_count": len(client_edges),
        "client_node_counts": np.bincount(homes, minlength=5).tolist(),
        "client_train_edge_counts": [len(edges) for edges in client_edges],
        "candidate_counts": {
            "positive": len(validation_positive),
            "negative": len(validation_negative),
            "intra": int(masks["intra"].sum()),
            "cross": int(masks["cross"].sum()),
        },
        "metrics": {
            method: evaluate_scores(labels, method_scores, masks)
            for method, method_scores in scores.items()
        },
    }


def summarize(records: list[dict], gate: dict) -> dict:
    candidate = gate["candidate"]
    summary = {
        "protocol": "P2_VALIDATION_v1",
        "test_accessed": False,
        "datasets": {},
    }
    all_gates: list[bool] = []
    for dataset in gate["advance_rule"]["datasets"]:
        subset = [record for record in records if record["dataset"] == dataset]
        dataset_summary = {"n": len(subset), "metrics": {}, "selected_public": {}}
        for metric in ("global", "intra", "cross"):
            means = {
                method: float(np.mean([r["metrics"][method][metric] for r in subset]))
                for method in subset[0]["metrics"]
            }
            public = max(gate["public_controls"], key=lambda method: means[method])
            candidate_values = np.asarray([r["metrics"][candidate][metric] for r in subset])
            public_values = np.asarray([r["metrics"][public][metric] for r in subset])
            dataset_summary["metrics"][metric] = {
                "means": means,
                "paired_candidate_vs_selected_public": paired_summary(
                    candidate_values, public_values
                ),
            }
            dataset_summary["selected_public"][metric] = public
            if metric in gate["advance_rule"]["metrics"]:
                passed = (
                    dataset_summary["metrics"][metric][
                        "paired_candidate_vs_selected_public"
                    ]["mean_difference"]
                    > gate["advance_rule"]["minimum_mean_paired_gain"]
                )
                dataset_summary["metrics"][metric]["validation_advance"] = passed
                all_gates.append(passed)
        summary["datasets"][dataset] = dataset_summary
    summary["decision"] = "ADVANCE_TO_TEST_FREEZE" if all(all_gates) else "NO_GO"
    return summary


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("validation output already exists; refusing overwrite")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    calibration = calibrate_gaussian(
        target_epsilon=config["privacy"]["epsilon"],
        delta=config["privacy"]["delta"],
        sensitivity=config["privacy"]["l2_sensitivity"],
        steps=config["privacy"]["releases"],
        orders=DEFAULT_ORDERS,
    )
    commit = git_head()
    records = [
        run_record(dataset, seed, calibration, commit)
        for dataset in config["datasets"]
        for seed in config["split"]["seeds"]
    ]
    OUTPUT.mkdir(parents=True)
    with (OUTPUT / "records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(
        json.dumps(summarize(records, gate), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
