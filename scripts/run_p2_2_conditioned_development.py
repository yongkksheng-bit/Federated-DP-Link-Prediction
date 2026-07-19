"""Run the frozen P2.2 conditioned-count candidates on validation only."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.conditioned_release import (
    conditioned_counts,
    conditioned_log_enrichment,
    public_capacity_layout,
    release_conditioned_counts,
    score_conditioned_pairs,
)
from fed_dp_lp.metrics import paired_summary
from fed_dp_lp.p2_data import (
    load_blogcatalog,
    load_facebook,
    load_lastfm,
    load_polblogs,
)
from fed_dp_lp.p2_pilot import (
    candidate_arrays,
    evaluate_scores,
    metric_masks,
    sparse_cosine_scores,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_2_conditioned_development.json"
P2_CONFIG = ROOT / "configs" / "p2_pilot.json"
P2_1_CONFIG = ROOT / "configs" / "p2_1_confirmatory.json"
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "results" / "p2_2_conditioned_development"


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dataset_spec(dataset: str, p2: dict, p2_1: dict):
    if dataset == "blogcatalog-v3":
        return (
            load_blogcatalog(RAW / dataset / "blogcatalog-v3.zip"),
            ROOT / "data" / "processed" / "p2_pilot" / dataset,
            p2["split"]["seeds"],
        )
    if dataset == "facebook-musae":
        return (
            load_facebook(RAW / dataset),
            ROOT / "data" / "processed" / "p2_pilot" / dataset,
            p2["split"]["seeds"],
        )
    if dataset == "polblogs-newman":
        return (
            load_polblogs(RAW / dataset / f"{dataset}.zip"),
            ROOT / "data" / "processed" / "p2_1_confirmatory" / dataset,
            p2_1["split"]["seeds"],
        )
    if dataset == "lastfm-asia-snap":
        return (
            load_lastfm(RAW / dataset / f"{dataset}.zip"),
            ROOT / "data" / "processed" / "p2_1_confirmatory" / dataset,
            p2_1["split"]["seeds"],
        )
    raise ValueError(dataset)


def local_count_vectors(train_positive, train_scores, homes, cells, layout, clients):
    owners = homes[train_positive[:, 0]]
    return tuple(
        conditioned_counts(
            train_positive[owners == client],
            cells,
            train_scores[owners == client],
            layout,
        )
        for client in range(clients)
    )


def run_dataset(dataset: str, config: dict, p2: dict, p2_1: dict, calibration, commit):
    graph, processed, seeds = dataset_spec(dataset, p2, p2_1)
    with np.load(processed / "public_layout.npz", allow_pickle=False) as source:
        homes, cells = source["homes"], source["cells"]
    layouts = {
        name: public_capacity_layout(
            graph.public_features,
            cells,
            np.asarray(edges),
            maximum_pairs=config["mechanism"]["public_capacity_sample_maximum"],
            seed=config["mechanism"]["public_capacity_seed"],
            dirichlet_alpha=config["mechanism"]["dirichlet_alpha"],
        )
        for name, edges in config["mechanism"]["bin_edges"].items()
    }
    records = []
    for seed in seeds:
        with np.load(
            processed / f"seed_{seed}_development.npz", allow_pickle=False
        ) as source:
            train_positive = source["train_positive"]
            positive = source["validation_positive"]
            negative = source["validation_negative"]
        pairs, labels = candidate_arrays(positive, negative)
        masks = metric_masks(pairs, homes)
        public = sparse_cosine_scores(graph.public_features, pairs)
        train_scores = sparse_cosine_scores(graph.public_features, train_positive)
        scores = {"public_cosine": public}
        release_metadata = {}
        for bin_name, layout in layouts.items():
            local = local_count_vectors(
                train_positive,
                train_scores,
                homes,
                cells,
                layout,
                p2["clients"],
            )
            rng = np.random.default_rng(
                np.random.SeedSequence([seed, 4201, layout.bins])
            )
            noisy = release_conditioned_counts(
                local,
                noise_std=calibration.noise_std,
                visibility="visible_messages",
                rng=rng,
            )
            residual = conditioned_log_enrichment(
                noisy,
                layout,
                alpha=config["mechanism"]["dirichlet_alpha"],
                clip=config["mechanism"]["log_enrichment_clip"],
            )
            release_metadata[bin_name] = {
                "release_dimension": layout.dimension,
                "capacity_sum": float(np.sum(layout.capacities)),
                "capacity_minimum": float(np.min(layout.capacities)),
                "local_l1_edge_counts": [float(np.sum(value)) for value in local],
            }
            for weight in config["mechanism"]["lambdas"]:
                name = f"conditioned_{bin_name}_lambda_{weight:g}"
                scores[name] = score_conditioned_pairs(
                    public,
                    pairs,
                    cells,
                    residual,
                    layout,
                    weight=weight,
                )
        records.append(
            {
                "protocol": "P2_2_CONDITIONED_DEVELOPMENT_v1",
                "code_commit": commit,
                "dataset": dataset,
                "seed": seed,
                "split": "validation",
                "test_accessed": False,
                "config_sha256": sha256(CONFIG),
                "privacy": asdict(calibration),
                "l2_sensitivity": 1.0,
                "client_count": p2["clients"],
                "client_node_counts": np.bincount(
                    homes, minlength=p2["clients"]
                ).tolist(),
                "public_capacity_sample_maximum": config["mechanism"]
                ["public_capacity_sample_maximum"],
                "release_metadata": release_metadata,
                "metrics": {
                    name: evaluate_scores(labels, values, masks)
                    for name, values in scores.items()
                },
            }
        )
    return records


def candidate_properties(candidate: str) -> tuple[int, float]:
    parts = candidate.split("_")
    return int(parts[1][1:]), float(parts[-1])


def summarize(records: list[dict], config: dict) -> dict:
    candidates = sorted(
        name for name in records[0]["metrics"] if name != "public_cosine"
    )
    all_candidates = {}
    for candidate in candidates:
        cells = {}
        for dataset in config["datasets"]:
            subset = [record for record in records if record["dataset"] == dataset]
            for metric in ("global", "cross"):
                observed = np.asarray(
                    [record["metrics"][candidate][metric] for record in subset]
                )
                reference = np.asarray(
                    [record["metrics"]["public_cosine"][metric] for record in subset]
                )
                summary = paired_summary(observed, reference)
                summary["candidate_mean"] = float(np.mean(observed))
                summary["public_mean"] = float(np.mean(reference))
                cells[f"{dataset}/{metric}"] = summary
        all_candidates[candidate] = cells

    selected = max(
        candidates,
        key=lambda candidate: (
            min(
                cell["mean_difference"]
                for cell in all_candidates[candidate].values()
            ),
            -candidate_properties(candidate)[0],
            -candidate_properties(candidate)[1],
        ),
    )
    selected_cells = all_candidates[selected]
    lastfm = [
        cell
        for name, cell in selected_cells.items()
        if name.startswith("lastfm-asia-snap/")
    ]
    bins, weight = candidate_properties(selected)
    checks = {
        "nonzero_lambda": weight > 0,
        "positive_all_eight_cells": all(
            cell["mean_difference"] > 0 for cell in selected_cells.values()
        ),
        "lastfm_global_and_cross_at_least_0p01": all(
            cell["mean_difference"] >= 0.01 for cell in lastfm
        ),
        "all_20_records_present": len(records) == 20,
        "no_test_access": all(not record["test_accessed"] for record in records),
    }
    return {
        "protocol": "P2_2_CONDITIONED_DEVELOPMENT_v1",
        "selection_criterion": config["selection"]["criterion"],
        "selected_candidate": selected,
        "selected_bins": bins,
        "selected_lambda": weight,
        "selected_cells": selected_cells,
        "checks": checks,
        "decision": (
            "ADVANCE_TO_NEW_CONFIRMATORY_SOURCE_REGISTRATION"
            if all(checks.values())
            else "REJECT_CONDITIONED_RELEASE"
        ),
        "test_accessed": False,
        "all_candidates": all_candidates,
    }


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("P2.2 output already exists; refusing overwrite")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    p2 = json.loads(P2_CONFIG.read_text(encoding="utf-8"))
    p2_1 = json.loads(P2_1_CONFIG.read_text(encoding="utf-8"))
    calibration = calibrate_gaussian(
        target_epsilon=config["privacy"]["epsilon"],
        delta=config["privacy"]["delta"],
        sensitivity=config["privacy"]["l2_sensitivity"],
        steps=config["privacy"]["releases"],
        orders=DEFAULT_ORDERS,
    )
    commit = git_head()
    records = []
    for dataset in config["datasets"]:
        records.extend(run_dataset(dataset, config, p2, p2_1, calibration, commit))
    OUTPUT.mkdir(parents=True)
    with (OUTPUT / "records.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(
        json.dumps(summarize(records, config), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
