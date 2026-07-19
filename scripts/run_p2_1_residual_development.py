"""Evaluate the frozen P2.1 simple residual family on validation only."""

from __future__ import annotations

import json
import pathlib
import subprocess
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.block_release import release_block_densities
from fed_dp_lp.metrics import paired_summary
from fed_dp_lp.p2_data import load_blogcatalog, load_facebook
from fed_dp_lp.p2_pilot import (
    candidate_arrays,
    evaluate_scores,
    metric_masks,
    sparse_cosine_scores,
)
from fed_dp_lp.public_views import repartition_edges
from fed_dp_lp.residual_release import residual_map, score_with_residual


ROOT = pathlib.Path(__file__).resolve().parents[1]
PILOT_CONFIG = ROOT / "configs" / "p2_pilot.json"
CONFIG = ROOT / "configs" / "p2_1_residual_development.json"
PROCESSED = ROOT / "data" / "processed" / "p2_pilot"
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "results" / "p2_1_residual_development"


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def load_graph(dataset: str):
    if dataset == "blogcatalog-v3":
        return load_blogcatalog(RAW / dataset / "blogcatalog-v3.zip")
    if dataset == "facebook-musae":
        return load_facebook(RAW / dataset)
    raise ValueError(dataset)


def run_record(dataset: str, seed: int, config: dict, calibration, commit: str) -> dict:
    graph = load_graph(dataset)
    with np.load(PROCESSED / dataset / "public_layout.npz", allow_pickle=False) as source:
        homes, cells = source["homes"], source["cells"]
    with np.load(
        PROCESSED / dataset / f"seed_{seed}_development.npz", allow_pickle=False
    ) as source:
        train_positive = source["train_positive"]
        positive = source["validation_positive"]
        negative = source["validation_negative"]
    pairs, labels = candidate_arrays(positive, negative)
    masks = metric_masks(pairs, homes)
    public = sparse_cosine_scores(graph.public_features, pairs)
    client_edges = repartition_edges(train_positive, homes, clients=5)
    rng = np.random.default_rng(np.random.SeedSequence([seed, 2101]))
    noisy_counts, _, layout = release_block_densities(
        client_edges,
        cells,
        noise_std=calibration.noise_std,
        visibility="visible_messages",
        rng=rng,
    )
    scores = {"public_cosine": public}
    for transform in config["residual_transforms"]:
        residuals = residual_map(noisy_counts, layout, transform=transform)
        for weight in config["lambdas"]:
            name = f"{transform}_lambda_{weight:g}"
            scores[name] = score_with_residual(
                public, pairs, cells, residuals, layout, weight=weight
            )
    return {
        "protocol": "P2_1_RESIDUAL_DEVELOPMENT_v1",
        "code_commit": commit,
        "dataset": dataset,
        "seed": seed,
        "split": "validation",
        "test_accessed": False,
        "privacy": asdict(calibration),
        "release_dimension": layout.dimension,
        "l2_sensitivity": 1.0,
        "metrics": {
            name: evaluate_scores(labels, values, masks) for name, values in scores.items()
        },
    }


def summarize(records: list[dict], config: dict) -> dict:
    datasets = sorted({record["dataset"] for record in records})
    candidates = sorted(
        method for method in records[0]["metrics"] if method != "public_cosine"
    )
    candidate_cells: dict[str, dict[str, dict]] = {}
    for candidate in candidates:
        cells = {}
        for dataset in datasets:
            subset = [record for record in records if record["dataset"] == dataset]
            for metric in ("global", "cross"):
                observed = np.asarray([r["metrics"][candidate][metric] for r in subset])
                public = np.asarray([r["metrics"]["public_cosine"][metric] for r in subset])
                cells[f"{dataset}/{metric}"] = paired_summary(observed, public)
        candidate_cells[candidate] = cells

    def weight(candidate: str) -> float:
        return float(candidate.rsplit("_", 1)[-1])

    def transform_order(candidate: str) -> int:
        return 0 if candidate.startswith("centered_block_rank") else 1

    selected = max(
        candidates,
        key=lambda candidate: (
            min(cell["mean_difference"] for cell in candidate_cells[candidate].values()),
            -weight(candidate),
            -transform_order(candidate),
        ),
    )
    selected_cells = candidate_cells[selected]
    facebook_cells = [
        cell for name, cell in selected_cells.items() if name.startswith("facebook-musae/")
    ]
    advance = (
        all(
            cell["mean_difference"] > config["advance_rule"]["minimum_gain_each_cell"]
            for cell in selected_cells.values()
        )
        and all(
            cell["mean_difference"]
            >= config["advance_rule"]["minimum_facebook_gain_each_primary_metric"]
            for cell in facebook_cells
        )
        and weight(selected) > 0
    )
    return {
        "protocol": "P2_1_RESIDUAL_DEVELOPMENT_v1",
        "test_accessed": False,
        "selection_criterion": config["selection"]["criterion"],
        "selected_candidate": selected,
        "selected_cells": selected_cells,
        "all_candidates": candidate_cells,
        "decision": "ADVANCE_TO_NEW_CONFIRMATORY_PROTOCOL" if advance else "REJECT_SIMPLE_RESIDUAL",
    }


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("P2.1 development output already exists; refusing overwrite")
    pilot = json.loads(PILOT_CONFIG.read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    calibration = calibrate_gaussian(
        target_epsilon=pilot["privacy"]["epsilon"],
        delta=pilot["privacy"]["delta"],
        sensitivity=pilot["privacy"]["l2_sensitivity"],
        steps=pilot["privacy"]["releases"],
        orders=DEFAULT_ORDERS,
    )
    commit = git_head()
    records = [
        run_record(dataset, seed, config, calibration, commit)
        for dataset in pilot["datasets"]
        for seed in pilot["split"]["seeds"]
    ]
    OUTPUT.mkdir(parents=True)
    with (OUTPUT / "records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(
        json.dumps(summarize(records, config), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
