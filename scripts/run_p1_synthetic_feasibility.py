"""Execute the frozen P1 synthetic feasibility protocol."""

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
from fed_dp_lp.block_release import (
    block_counts,
    make_block_layout,
    release_block_densities,
    score_pairs,
)
from fed_dp_lp.metrics import paired_summary, roc_auc
from fed_dp_lp.synthetic import generate_sbm


OUTPUT = ROOT / "results" / "p1_synthetic"
SEEDS = tuple(range(30))
DOMAINS = {
    "social_assortative": {
        "nodes": 240,
        "groups_count": 4,
        "clients": 5,
        "within_probability": 0.18,
        "between_probability": 0.025,
        "train_retention": 0.70,
    },
    "blog_mixed": {
        "nodes": 300,
        "groups_count": 5,
        "clients": 5,
        "within_probability": 0.12,
        "between_probability": 0.045,
        "train_retention": 0.65,
    },
}
TARGET_EPSILON = 4.0
DELTA = 1e-6


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def metric_slices(pairs: np.ndarray, homes: np.ndarray) -> dict[str, np.ndarray]:
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    return {
        "global": np.ones(len(pairs), dtype=bool),
        "intra": ~cross,
        "cross": cross,
    }


def evaluate(labels: np.ndarray, scores: np.ndarray, masks: dict[str, np.ndarray]) -> dict[str, float]:
    return {name: roc_auc(labels[mask], scores[mask]) for name, mask in masks.items()}


def run_one(domain: str, config: dict[str, float], seed: int, commit: str, calibration) -> dict:
    graph = generate_sbm(seed=seed, **config)
    pairs = np.concatenate([graph.positive_pairs, graph.negative_pairs], axis=0)
    labels = np.concatenate(
        [np.ones(len(graph.positive_pairs), dtype=int), np.zeros(len(graph.negative_pairs), dtype=int)]
    )
    masks = metric_slices(pairs, graph.homes)
    layout = make_block_layout(graph.groups)
    total_counts = sum(
        (block_counts(edges, graph.groups, layout) for edges in graph.client_edges),
        start=np.zeros(layout.dimension),
    )
    nonprivate_density = total_counts / layout.capacities

    random_rng = np.random.default_rng(np.random.SeedSequence([seed, 1001]))
    scores = {
        "public_only": np.zeros(len(pairs)),
        "random": random_rng.random(len(pairs)),
        "nonprivate_oracle": graph.true_probabilities,
        "nonprivate_counts": score_pairs(pairs, graph.groups, nonprivate_density, layout),
    }
    for visibility, stream in (("ideal_secagg", 2001), ("visible_messages", 3001)):
        rng = np.random.default_rng(np.random.SeedSequence([seed, stream]))
        _, density, released_layout = release_block_densities(
            graph.client_edges,
            graph.groups,
            noise_std=calibration.noise_std,
            visibility=visibility,
            rng=rng,
        )
        scores[f"dp_block_counts_{visibility}"] = score_pairs(
            pairs, graph.groups, density, released_layout
        )

    return {
        "protocol": "P1_SYNTHETIC_FEASIBILITY_PROTOCOL_v1",
        "source_commit": commit,
        "domain": domain,
        "seed": seed,
        "config": config,
        "privacy": asdict(calibration),
        "release_dimension": layout.dimension,
        "l2_sensitivity": 1.0,
        "client_sizes": [int(len(x)) for x in graph.client_edges],
        "training_edges": int(sum(len(x) for x in graph.client_edges)),
        "candidate_counts": {
            "positive": int(len(graph.positive_pairs)),
            "negative": int(len(graph.negative_pairs)),
            "intra": int(np.sum(masks["intra"])),
            "cross": int(np.sum(masks["cross"])),
        },
        "metrics": {name: evaluate(labels, value, masks) for name, value in scores.items()},
    }


def summarize(records: list[dict]) -> dict:
    summary = {"protocol": "P1_SYNTHETIC_FEASIBILITY_PROTOCOL_v1", "domains": {}}
    primary = "dp_block_counts_ideal_secagg"
    for domain in DOMAINS:
        subset = [record for record in records if record["domain"] == domain]
        domain_summary = {"n": len(subset), "metrics": {}, "gates": {}}
        methods = subset[0]["metrics"]
        for metric in ("global", "intra", "cross"):
            domain_summary["metrics"][metric] = {
                method: {
                    "mean": float(np.mean([r["metrics"][method][metric] for r in subset])),
                    "std": float(np.std([r["metrics"][method][metric] for r in subset], ddof=1)),
                }
                for method in methods
            }
            observed = np.asarray([r["metrics"][primary][metric] for r in subset])
            for reference in ("public_only", "random", "nonprivate_oracle"):
                baseline = np.asarray([r["metrics"][reference][metric] for r in subset])
                domain_summary["metrics"][metric][f"paired_vs_{reference}"] = paired_summary(
                    observed, baseline
                )

        global_public = domain_summary["metrics"]["global"]["paired_vs_public_only"]
        cross_public = domain_summary["metrics"]["cross"]["paired_vs_public_only"]
        global_random = domain_summary["metrics"]["global"]["paired_vs_random"]
        cross_random = domain_summary["metrics"]["cross"]["paired_vs_random"]
        global_oracle = domain_summary["metrics"]["global"]["paired_vs_nonprivate_oracle"]
        cross_oracle = domain_summary["metrics"]["cross"]["paired_vs_nonprivate_oracle"]
        domain_summary["gates"] = {
            "global_public_effect_ge_0p02": global_public["mean_difference"] >= 0.02,
            "cross_public_effect_ge_0p02": cross_public["mean_difference"] >= 0.02,
            "global_public_ci_excludes_zero": global_public["ci95_low"] > 0,
            "cross_public_ci_excludes_zero": cross_public["ci95_low"] > 0,
            "global_random_ci_excludes_zero": global_random["ci95_low"] > 0,
            "cross_random_ci_excludes_zero": cross_random["ci95_low"] > 0,
            "global_oracle_excess_le_0p02": global_oracle["mean_difference"] <= 0.02,
            "cross_oracle_excess_le_0p02": cross_oracle["mean_difference"] <= 0.02,
        }
        domain_summary["pass"] = all(domain_summary["gates"].values())
        summary["domains"][domain] = domain_summary
    summary["decision"] = (
        "GO" if all(item["pass"] for item in summary["domains"].values()) else "NO_GO"
    )
    return summary


def main() -> None:
    calibration = calibrate_gaussian(
        target_epsilon=TARGET_EPSILON,
        delta=DELTA,
        sensitivity=1.0,
        steps=1,
        orders=DEFAULT_ORDERS,
    )
    commit = git_commit()
    records = [
        run_one(domain, config, seed, commit, calibration)
        for domain, config in DOMAINS.items()
        for seed in SEEDS
    ]
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
