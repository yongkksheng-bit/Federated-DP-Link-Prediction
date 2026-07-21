"""Execute the frozen P4R RAP synthetic feasibility gate."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
from dataclasses import asdict

import numpy as np

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.gap_adaptation import (
    normalize_rows,
    release_private_aggregations,
    score_pairs_from_channels,
    undirected_adjacency,
)
from fed_dp_lp.generalized_synthetic import generate_reciprocal_preference_graph
from fed_dp_lp.metrics import paired_summary, roc_auc
from fed_dp_lp.reciprocal_profile import (
    RAP_L2_SENSITIVITY,
    joint_profile_scales,
    reciprocal_profile_counts,
    release_joint_semantic_profile,
    score_rap_pairs,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p4r_rap_synthetic.json"
OUTPUT = ROOT / "results/p4r_rap_synthetic"
STREAM = 20260731


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def masks_for(pairs, homes):
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    return {"global": np.ones(len(pairs), dtype=bool), "intra": ~cross, "cross": cross}


def metrics(labels, scores, masks):
    return {scope: {"roc_auc": roc_auc(labels[mask], scores[mask])}
            for scope, mask in masks.items()}


def local_profiles(client_edges, cells, nodes):
    return tuple(
        reciprocal_profile_counts(edges, cells, node_count=nodes)
        for edges in client_edges
    )


def prepare(domain_config, seed):
    graph = generate_reciprocal_preference_graph(seed=seed, **domain_config)
    pairs = np.concatenate([graph.positive_pairs, graph.negative_pairs], axis=0)
    labels = np.concatenate([
        np.ones(len(graph.positive_pairs), dtype=np.int64),
        np.zeros(len(graph.negative_pairs), dtype=np.int64),
    ])
    adjacency = undirected_adjacency(graph.client_edges, len(graph.public_cells))
    return graph, {
        "pairs": pairs,
        "labels": labels,
        "masks": masks_for(pairs, graph.homes),
        "adjacency": adjacency,
        "profiles": local_profiles(
            graph.client_edges, graph.public_cells, len(graph.public_cells)
        ),
    }


def gap_scores(graph, state, calibration, domain_index, seed):
    rng = np.random.default_rng(np.random.SeedSequence([STREAM, domain_index, seed]))
    channels = release_private_aggregations(
        graph.client_edges,
        graph.public_features,
        hops=1,
        noise_std=calibration.noise_std,
        visibility="visible_messages",
        rng=rng,
        adjacency=state["adjacency"],
    )
    return score_pairs_from_channels(channels, state["pairs"])


def rap_scores(graph, state, calibration, domain_index, seed, gamma, weight, prior):
    # Reuse the GAP stream so the semantic Gaussian matrix is exactly coupled.
    rng = np.random.default_rng(np.random.SeedSequence([STREAM, domain_index, seed]))
    semantic, profiles = release_joint_semantic_profile(
        state["adjacency"],
        graph.public_features,
        state["profiles"],
        profile_energy_fraction=gamma,
        noise_std=calibration.noise_std,
        visibility="visible_messages",
        rng=rng,
    )
    _, profile_scale = joint_profile_scales(gamma)
    effective_profile_noise = (
        calibration.noise_std * np.sqrt(len(graph.client_edges)) / profile_scale
    )
    channels = (normalize_rows(graph.public_features), normalize_rows(semantic))
    return score_rap_pairs(
        channels,
        profiles,
        state["pairs"],
        graph.public_cells,
        profile_weight=weight,
        prior_strength=prior,
        effective_profile_noise_std=effective_profile_noise,
    )


def key(record):
    return (
        record["profile_energy_fraction"],
        record["profile_weight"],
        record["prior_strength"],
    )


def select_config(records, config):
    candidates = []
    for candidate in sorted(set(key(record) for record in records)):
        domain_gains = []
        for domain in config["domains"]:
            subset = [r for r in records if r["domain"] == domain and key(r) == candidate]
            domain_gains.append(float(np.mean([
                r["rap_global_roc_auc"] - r["gap_global_roc_auc"] for r in subset
            ])))
        gamma, weight, prior = candidate
        candidates.append((
            -min(domain_gains), gamma, weight, -prior, candidate, domain_gains
        ))
    selected = min(candidates)
    return selected[-2], {
        domain: gain for domain, gain in zip(config["domains"], selected[-1])
    }


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def main():
    if OUTPUT.exists():
        raise SystemExit("P4R synthetic output exists; refusing overwrite")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    calibration = calibrate_gaussian(
        target_epsilon=config["privacy"]["epsilon"],
        delta=config["privacy"]["delta"],
        sensitivity=RAP_L2_SENSITIVITY,
        steps=config["privacy"]["releases"],
        orders=DEFAULT_ORDERS,
    )
    commit = git_head()
    selection_records = []
    for domain_index, (domain, domain_config) in enumerate(config["domains"].items()):
        for seed in config["seeds"]["selection"]:
            graph, state = prepare(domain_config, seed)
            gap = gap_scores(graph, state, calibration, domain_index, seed)
            gap_auc = roc_auc(state["labels"], gap)
            for gamma in config["grid"]["profile_energy_fractions"]:
                for weight in config["grid"]["profile_weights"]:
                    for prior in config["grid"]["prior_strengths"]:
                        rap = rap_scores(
                            graph, state, calibration, domain_index, seed,
                            gamma, weight, prior,
                        )
                        selection_records.append({
                            "domain": domain,
                            "seed": seed,
                            "profile_energy_fraction": gamma,
                            "profile_weight": weight,
                            "prior_strength": prior,
                            "gap_global_roc_auc": gap_auc,
                            "rap_global_roc_auc": roc_auc(state["labels"], rap),
                        })
    selected, selection_domain_gains = select_config(selection_records, config)
    gamma, weight, prior = selected
    held_records = []
    for domain_index, (domain, domain_config) in enumerate(config["domains"].items()):
        for seed in config["seeds"]["held_out"]:
            graph, state = prepare(domain_config, seed)
            gap = gap_scores(graph, state, calibration, domain_index, seed)
            rap = rap_scores(
                graph, state, calibration, domain_index, seed,
                gamma, weight, prior,
            )
            public = score_pairs_from_channels(
                (normalize_rows(graph.public_features),), state["pairs"]
            )
            held_records.append({
                "protocol": config["protocol"],
                "role": "held_out_synthetic_feasibility",
                "code_commit": commit,
                "config_sha256": sha256(CONFIG_PATH),
                "domain": domain,
                "seed": seed,
                "real_graph_accessed": False,
                "privacy": asdict(calibration),
                "l2_sensitivity": RAP_L2_SENSITIVITY,
                "visibility": "individually_visible_client_messages",
                "semantic_noise_coupled_with_gap": True,
                "selected_config": {
                    "profile_energy_fraction": gamma,
                    "profile_weight": weight,
                    "prior_strength": prior,
                },
                "client_edge_counts": [len(x) for x in graph.client_edges],
                "profile_dimension": len(graph.public_cells)
                * domain_config["cells_count"],
                "metrics": {
                    "rap": metrics(state["labels"], rap, state["masks"]),
                    "gap": metrics(state["labels"], gap, state["masks"]),
                    "public_cosine": metrics(state["labels"], public, state["masks"]),
                    "probability_oracle": metrics(
                        state["labels"], graph.true_probabilities, state["masks"]
                    ),
                },
            })
    comparisons = {}
    checks = {}
    gate = config["go_no_go"]
    for domain in config["domains"]:
        rows = [r for r in held_records if r["domain"] == domain]
        comparisons[domain] = {}
        for scope in ("global", "cross"):
            rap = np.asarray([r["metrics"]["rap"][scope]["roc_auc"] for r in rows])
            gap = np.asarray([r["metrics"]["gap"][scope]["roc_auc"] for r in rows])
            comparisons[domain][scope] = paired_summary(rap, gap)
        checks[f"{domain}_global_gain"] = (
            comparisons[domain]["global"]["mean_difference"]
            >= gate["minimum_global_gain_each_domain"]
        )
        checks[f"{domain}_cross_gain"] = (
            comparisons[domain]["cross"]["mean_difference"]
            >= gate["minimum_cross_gain_each_domain"]
        )
        checks[f"{domain}_global_ci"] = comparisons[domain]["global"]["ci95_low"] > 0
        checks[f"{domain}_cross_ci"] = comparisons[domain]["cross"]["ci95_low"] > 0
    checks["all_metrics_finite"] = all(
        np.isfinite(value) for record in held_records
        for method in record["metrics"].values()
        for scope in method.values() for value in scope.values()
    )
    checks["no_real_graph_access"] = all(
        not record["real_graph_accessed"] for record in held_records
    )
    decision = "GO_TO_NEW_REAL_DATA_DEVELOPMENT_PROTOCOL" if all(checks.values()) else "NO_GO_REJECT_RAP"
    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "selection_records.jsonl", selection_records)
    write_jsonl(OUTPUT / "held_out_records.jsonl", held_records)
    (OUTPUT / "summary.json").write_text(json.dumps({
        "protocol": config["protocol"],
        "selection_record_count": len(selection_records),
        "held_out_record_count": len(held_records),
        "selected_config": {
            "profile_energy_fraction": gamma,
            "profile_weight": weight,
            "prior_strength": prior,
        },
        "selection_domain_gains": selection_domain_gains,
        "comparisons_vs_gap": comparisons,
        "checks": checks,
        "decision": decision,
        "real_graph_accessed": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
