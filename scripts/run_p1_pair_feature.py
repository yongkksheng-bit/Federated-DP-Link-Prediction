"""Run the preregistered P1 soft pair-feature release experiment."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.block_release import release_block_densities, score_pairs
from fed_dp_lp.generalized_synthetic import generate_generalized_sbm
from fed_dp_lp.metrics import paired_summary, roc_auc
from fed_dp_lp.pair_release import (
    fit_public_ridge,
    release_pair_statistic,
    symmetric_pair_features,
)


OUTPUT = ROOT / "results" / "p1_pair_feature"
SEEDS = tuple(range(30))
EPSILONS = (1.0, 2.0, 4.0)
CORRUPTIONS = (0.25, 0.5, 1.0)
VISIBILITIES = ("ideal_secagg", "visible_messages")
DELTA = 1e-6
DOMAINS = {
    "heterophilic_social": {
        "nodes": 320,
        "clients": 5,
        "train_retention": 0.65,
        "affinity": np.asarray([
            [0.025, 0.180, 0.040, 0.140],
            [0.180, 0.030, 0.150, 0.035],
            [0.040, 0.150, 0.025, 0.170],
            [0.140, 0.035, 0.170, 0.030],
        ]),
    },
    "mixed_blog": {
        "nodes": 360,
        "clients": 5,
        "train_retention": 0.65,
        "affinity": np.asarray([
            [0.120, 0.020, 0.140, 0.040, 0.080],
            [0.020, 0.030, 0.050, 0.150, 0.040],
            [0.140, 0.050, 0.100, 0.020, 0.130],
            [0.040, 0.150, 0.020, 0.040, 0.110],
            [0.080, 0.040, 0.130, 0.110, 0.080],
        ]),
    },
}


def source_commit():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def metric_masks(pairs, homes):
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    return {"global": np.ones(len(pairs), dtype=bool), "intra": ~cross, "cross": cross}


def evaluate(labels, scores, masks):
    return {name: roc_auc(labels[mask], scores[mask]) for name, mask in masks.items()}


def contiguous_argmax(features):
    raw = np.argmax(features, axis=1)
    _, inverse = np.unique(raw, return_inverse=True)
    return inverse.astype(np.int64)


def build_records():
    calibrations = {
        epsilon: calibrate_gaussian(
            target_epsilon=epsilon, delta=DELTA, sensitivity=1.0, steps=1,
            orders=DEFAULT_ORDERS,
        )
        for epsilon in EPSILONS
    }
    commit = source_commit()
    records = []
    for domain, config in DOMAINS.items():
        for seed in SEEDS:
            for corruption in CORRUPTIONS:
                graph = generate_generalized_sbm(
                    seed=seed, feature_corruption=corruption, **config
                )
                all_edges = np.concatenate(graph.client_edges, axis=0)
                all_pairs = np.asarray([
                    (u, v) for u in range(config["nodes"])
                    for v in range(u + 1, config["nodes"])
                ], dtype=np.int64)
                candidates = np.concatenate(
                    [graph.positive_pairs, graph.negative_pairs], axis=0
                )
                labels = np.concatenate([
                    np.ones(len(graph.positive_pairs), dtype=int),
                    np.zeros(len(graph.negative_pairs), dtype=int),
                ])
                masks = metric_masks(candidates, graph.homes)
                all_design = symmetric_pair_features(graph.public_features, all_pairs)
                candidate_design = symmetric_pair_features(graph.public_features, candidates)
                hard_groups = contiguous_argmax(graph.public_features)
                cosine = np.sum(
                    graph.public_features[candidates[:, 0]]
                    * graph.public_features[candidates[:, 1]], axis=1
                )
                same_hard = (
                    hard_groups[candidates[:, 0]] == hard_groups[candidates[:, 1]]
                ).astype(float)
                public_scores = {
                    "public_constant": np.zeros(len(candidates)),
                    "public_cosine": cosine,
                    "public_negative_cosine": -cosine,
                    "public_same_hard": same_hard,
                    "public_different_hard": 1.0 - same_hard,
                    "random": np.random.default_rng(
                        np.random.SeedSequence([seed, 701])
                    ).random(len(candidates)),
                    "oracle": graph.true_probabilities,
                }
                for epsilon in EPSILONS:
                    calibration = calibrations[epsilon]
                    for visibility in VISIBILITIES:
                        stream = (
                            int(epsilon * 1000) + int(corruption * 10000)
                            + (10_000_000 if visibility == "visible_messages" else 0)
                        )
                        soft_rng = np.random.default_rng(
                            np.random.SeedSequence([seed, stream, 801])
                        )
                        released = release_pair_statistic(
                            graph.client_edges, graph.public_features,
                            noise_std=calibration.noise_std, visibility=visibility,
                            rng=soft_rng,
                        )
                        weights = fit_public_ridge(all_design, released)
                        soft_scores = candidate_design @ weights
                        hard_rng = np.random.default_rng(
                            np.random.SeedSequence([seed, stream, 802])
                        )
                        _, hard_density, hard_layout = release_block_densities(
                            graph.client_edges, hard_groups,
                            noise_std=calibration.noise_std, visibility=visibility,
                            rng=hard_rng,
                        )
                        hard_scores = score_pairs(
                            candidates, hard_groups, hard_density, hard_layout
                        )
                        methods = {
                            "soft_pair_dp": soft_scores,
                            "hard_group_dp": hard_scores,
                            **public_scores,
                        }
                        records.append({
                            "protocol": "P1_PAIR_FEATURE_PROTOCOL_v1",
                            "source_commit": commit,
                            "domain": domain,
                            "seed": seed,
                            "epsilon_target": epsilon,
                            "feature_corruption": corruption,
                            "visibility": visibility,
                            "privacy": asdict(calibration),
                            "release_dimension": int(released.size),
                            "l2_sensitivity": 1.0,
                            "clients": config["clients"],
                            "client_sizes": [int(len(item)) for item in graph.client_edges],
                            "training_edges": int(len(all_edges)),
                            "candidate_counts": {
                                "positive": int(len(graph.positive_pairs)),
                                "negative": int(len(graph.negative_pairs)),
                                "cross": int(np.sum(masks["cross"])),
                            },
                            "metrics": {
                                method: evaluate(labels, scores, masks)
                                for method, scores in methods.items()
                            },
                        })
    return records


def summarize(records):
    grouped = {}
    for record in records:
        key = (
            record["domain"], record["epsilon_target"],
            record["feature_corruption"], record["visibility"],
        )
        grouped.setdefault(key, []).append(record)
    cells = []
    methods = tuple(records[0]["metrics"])
    for key, items in sorted(grouped.items()):
        domain, epsilon, corruption, visibility = key
        metrics = {}
        for metric in ("global", "intra", "cross"):
            metrics[metric] = {}
            candidate = np.asarray([
                item["metrics"]["soft_pair_dp"][metric] for item in items
            ])
            for method in methods:
                values = np.asarray([item["metrics"][method][metric] for item in items])
                metrics[metric][method] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values, ddof=1)),
                }
                if method != "soft_pair_dp":
                    metrics[metric][f"paired_soft_vs_{method}"] = paired_summary(
                        candidate, values
                    )
        cells.append({
            "domain": domain, "epsilon": epsilon,
            "feature_corruption": corruption, "visibility": visibility,
            "n": len(items), "metrics": metrics,
        })

    public_methods = (
        "public_constant", "public_cosine", "public_negative_cosine",
        "public_same_hard", "public_different_hard",
    )
    gate_checks = []
    for cell in cells:
        required_public = (
            cell["visibility"] == "ideal_secagg" and cell["epsilon"] >= 2
            and cell["feature_corruption"] <= 0.5
        )
        if required_public:
            checks = {}
            for metric in ("global", "cross"):
                for method in public_methods:
                    paired = cell["metrics"][metric][f"paired_soft_vs_{method}"]
                    checks[f"{metric}_vs_{method}_effect"] = paired["mean_difference"] >= 0.02
                    checks[f"{metric}_vs_{method}_ci"] = paired["ci95_low"] > 0
            gate_checks.append({"type": "public_utility", "cell": {
                key: cell[key] for key in (
                    "domain", "epsilon", "feature_corruption", "visibility"
                )
            }, "checks": checks, "pass": all(checks.values())})

        if (
            cell["visibility"] == "ideal_secagg" and cell["epsilon"] == 4
            and cell["feature_corruption"] == 0.5
        ):
            checks = {}
            for metric in ("global", "cross"):
                paired = cell["metrics"][metric]["paired_soft_vs_hard_group_dp"]
                checks[f"{metric}_hard_noninferiority"] = paired["mean_difference"] >= -0.02
            gate_checks.append({"type": "hard_noninferiority", "cell": {
                key: cell[key] for key in (
                    "domain", "epsilon", "feature_corruption", "visibility"
                )
            }, "checks": checks, "pass": all(checks.values())})

        if (
            cell["visibility"] == "ideal_secagg" and cell["epsilon"] == 4
            and cell["feature_corruption"] == 1.0
        ):
            paired = cell["metrics"]["cross"]["paired_soft_vs_hard_group_dp"]
            checks = {"cross_hard_superiority": paired["mean_difference"] > 0}
            gate_checks.append({"type": "hard_superiority", "cell": {
                key: cell[key] for key in (
                    "domain", "epsilon", "feature_corruption", "visibility"
                )
            }, "checks": checks, "pass": all(checks.values())})

    return {
        "protocol": "P1_PAIR_FEATURE_PROTOCOL_v1",
        "record_count": len(records), "cell_count": len(cells),
        "cells": cells, "gate_checks": gate_checks,
        "decision": "ADVANCE" if all(item["pass"] for item in gate_checks) else "REJECT",
    }


def main():
    records = build_records()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(
        json.dumps(summarize(records), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
