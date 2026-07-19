"""Execute the frozen P1 synthetic stress-test matrix."""

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
from fed_dp_lp.metrics import paired_summary, roc_auc
from fed_dp_lp.public_views import (
    balanced_labels,
    corrupt_groups,
    refine_groups,
    repartition_edges,
)
from fed_dp_lp.synthetic import generate_sbm


OUTPUT = ROOT / "results" / "p1_stress"
SEEDS = tuple(range(20))
EPSILONS = (0.5, 1.0, 2.0, 4.0, 8.0)
CORRUPTIONS = (0.0, 0.10, 0.25, 0.50)
REFINEMENTS = (1, 2, 4)
CLIENT_COUNTS = (2, 5, 10, 20)
DELTA = 1e-6
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


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def auc_metrics(labels, scores, pairs, homes):
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    masks = {"global": np.ones(len(pairs), dtype=bool), "intra": ~cross, "cross": cross}
    return {name: roc_auc(labels[mask], scores[mask]) for name, mask in masks.items()}


def one_record(
    *, domain, seed, axis, epsilon, corruption, refinement, clients, visibility,
    graph, all_edges, pairs, labels, public_groups, homes, client_edges,
    calibration, commit,
):
    stream = int(round(epsilon * 1000)) + int(corruption * 10000) + refinement * 100000
    if visibility == "visible_messages":
        stream += 10_000_000
    # Reuse the same ideal aggregate noise across K to isolate home partitioning.
    if axis != "federation_scaling" or visibility == "visible_messages":
        stream += clients * 1_000_000
    rng = np.random.default_rng(np.random.SeedSequence([seed, stream]))
    _, densities, layout = release_block_densities(
        client_edges,
        public_groups,
        noise_std=calibration.noise_std,
        visibility=visibility,
        rng=rng,
    )
    dp_scores = score_pairs(pairs, public_groups, densities, layout)
    random_scores = np.random.default_rng(np.random.SeedSequence([seed, 991])).random(len(pairs))
    return {
        "protocol": "P1_STRESS_TEST_PROTOCOL_v1",
        "source_commit": commit,
        "domain": domain,
        "seed": seed,
        "axis": axis,
        "epsilon_target": epsilon,
        "corruption": corruption,
        "refinement": refinement,
        "clients": clients,
        "visibility": visibility,
        "privacy": asdict(calibration),
        "release_dimension": layout.dimension,
        "l2_sensitivity": 1.0,
        "training_edges": int(len(all_edges)),
        "client_sizes": [int(len(item)) for item in client_edges],
        "candidate_counts": {
            "positive": int(len(graph.positive_pairs)),
            "negative": int(len(graph.negative_pairs)),
            "cross": int(np.sum(homes[pairs[:, 0]] != homes[pairs[:, 1]])),
        },
        "metrics": {
            "dp": auc_metrics(labels, dp_scores, pairs, homes),
            "public_only": auc_metrics(labels, np.zeros(len(pairs)), pairs, homes),
            "random": auc_metrics(labels, random_scores, pairs, homes),
            "oracle": auc_metrics(labels, graph.true_probabilities, pairs, homes),
        },
    }


def build_records():
    calibrations = {
        epsilon: calibrate_gaussian(
            target_epsilon=epsilon,
            delta=DELTA,
            sensitivity=1.0,
            steps=1,
            orders=DEFAULT_ORDERS,
        )
        for epsilon in EPSILONS
    }
    commit = source_commit()
    records = []
    for domain, config in DOMAINS.items():
        for seed in SEEDS:
            graph = generate_sbm(seed=seed, **config)
            all_edges = np.concatenate(graph.client_edges, axis=0)
            pairs = np.concatenate([graph.positive_pairs, graph.negative_pairs], axis=0)
            labels = np.concatenate([
                np.ones(len(graph.positive_pairs), dtype=int),
                np.zeros(len(graph.negative_pairs), dtype=int),
            ])

            for corruption in CORRUPTIONS:
                group_rng = np.random.default_rng(np.random.SeedSequence([seed, 110, int(corruption * 100)]))
                public_groups = corrupt_groups(graph.groups, corruption, group_rng)
                for epsilon in EPSILONS:
                    records.append(one_record(
                        domain=domain, seed=seed, axis="privacy_misspecification",
                        epsilon=epsilon, corruption=corruption, refinement=1,
                        clients=5, visibility="ideal_secagg", graph=graph,
                        all_edges=all_edges, pairs=pairs, labels=labels,
                        public_groups=public_groups, homes=graph.homes,
                        client_edges=graph.client_edges, calibration=calibrations[epsilon],
                        commit=commit,
                    ))

            for refinement in REFINEMENTS:
                group_rng = np.random.default_rng(np.random.SeedSequence([seed, 220, refinement]))
                public_groups = refine_groups(graph.groups, refinement, group_rng)
                for epsilon in (1.0, 4.0):
                    for visibility in ("ideal_secagg", "visible_messages"):
                        records.append(one_record(
                            domain=domain, seed=seed, axis="release_dimension",
                            epsilon=epsilon, corruption=0.0, refinement=refinement,
                            clients=5, visibility=visibility, graph=graph,
                            all_edges=all_edges, pairs=pairs, labels=labels,
                            public_groups=public_groups, homes=graph.homes,
                            client_edges=graph.client_edges, calibration=calibrations[epsilon],
                            commit=commit,
                        ))

            public_groups = refine_groups(
                graph.groups, 4, np.random.default_rng(np.random.SeedSequence([seed, 330, 4]))
            )
            for clients in CLIENT_COUNTS:
                homes = balanced_labels(
                    len(graph.groups), clients,
                    np.random.default_rng(np.random.SeedSequence([seed, 440, clients])),
                )
                client_edges = repartition_edges(all_edges, homes, clients)
                for visibility in ("ideal_secagg", "visible_messages"):
                    records.append(one_record(
                        domain=domain, seed=seed, axis="federation_scaling",
                        epsilon=4.0, corruption=0.0, refinement=4,
                        clients=clients, visibility=visibility, graph=graph,
                        all_edges=all_edges, pairs=pairs, labels=labels,
                        public_groups=public_groups, homes=homes,
                        client_edges=client_edges, calibration=calibrations[4.0],
                        commit=commit,
                    ))
    return records


def cell_key(record):
    return (
        record["domain"], record["axis"], record["epsilon_target"],
        record["corruption"], record["refinement"], record["clients"],
        record["visibility"],
    )


def summarize(records):
    cells = {}
    for record in records:
        cells.setdefault(cell_key(record), []).append(record)
    summaries = []
    for key, items in sorted(cells.items()):
        domain, axis, epsilon, corruption, refinement, clients, visibility = key
        metric_summary = {}
        for metric in ("global", "intra", "cross"):
            dp = np.asarray([item["metrics"]["dp"][metric] for item in items])
            metric_summary[metric] = {
                "dp_mean": float(np.mean(dp)),
                "dp_std": float(np.std(dp, ddof=1)),
            }
            for reference in ("public_only", "random", "oracle"):
                baseline = np.asarray([item["metrics"][reference][metric] for item in items])
                metric_summary[metric][f"paired_vs_{reference}"] = paired_summary(dp, baseline)
        summaries.append({
            "domain": domain, "axis": axis, "epsilon": epsilon,
            "corruption": corruption, "refinement": refinement,
            "clients": clients, "visibility": visibility,
            "n": len(items), "metrics": metric_summary,
        })

    gate_cells = []
    for cell in summaries:
        required = (
            (cell["axis"] == "privacy_misspecification" and cell["epsilon"] >= 2
             and cell["corruption"] <= 0.25)
            or
            (cell["axis"] == "release_dimension" and cell["epsilon"] == 4
             and cell["refinement"] <= 2 and cell["visibility"] == "ideal_secagg")
        )
        if not required:
            continue
        checks = {}
        for metric in ("global", "cross"):
            paired = cell["metrics"][metric]["paired_vs_public_only"]
            checks[f"{metric}_effect_ge_0p02"] = paired["mean_difference"] >= 0.02
            checks[f"{metric}_ci_excludes_zero"] = paired["ci95_low"] > 0
        gate_cells.append({"cell": {k: cell[k] for k in (
            "domain", "axis", "epsilon", "corruption", "refinement", "clients", "visibility"
        )}, "checks": checks, "pass": all(checks.values())})
    return {
        "protocol": "P1_STRESS_TEST_PROTOCOL_v1",
        "record_count": len(records),
        "cell_count": len(summaries),
        "cells": summaries,
        "gate_cells": gate_cells,
        "decision": "ADVANCE" if all(cell["pass"] for cell in gate_cells) else "STOP",
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
