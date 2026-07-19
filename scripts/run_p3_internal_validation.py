"""Run the frozen P3.1 internal mechanism matrix on validation only."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import time
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
from fed_dp_lp.metrics import average_precision, paired_summary, roc_auc
from fed_dp_lp.p2_pilot import candidate_arrays, metric_masks, sparse_cosine_scores
from fed_dp_lp.p3_data import load_p3_graph
from fed_dp_lp.systems import logical_payload_bytes, peak_resident_memory_bytes


ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER = ROOT / "configs" / "p3_master_benchmark.json"
CONFIG = ROOT / "configs" / "p3_internal_validation.json"
SOURCE_CONTRACT = ROOT / "data" / "manifests" / "p3_source_contract.json"
SPLIT_MANIFEST = ROOT / "data" / "manifests" / "p3_split_manifest.json"
SPLIT_AUDIT = ROOT / "data" / "manifests" / "p3_split_audit.json"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "p3_benchmark"
OUTPUT = ROOT / "results" / "p3_internal_validation"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def ranking_metrics(labels, scores, masks):
    result = {}
    for scope, mask in masks.items():
        result[scope] = {
            "roc_auc": roc_auc(labels[mask], scores[mask]),
            "average_precision": average_precision(labels[mask], scores[mask]),
        }
    return result


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


def release_and_score(
    local,
    public,
    pairs,
    cells,
    layout,
    master,
    *,
    calibration,
    visibility,
    seed,
    epsilon_index,
    stream,
):
    started = time.perf_counter()
    rng = np.random.default_rng(
        np.random.SeedSequence([seed, epsilon_index, stream])
    )
    noisy = release_conditioned_counts(
        local,
        noise_std=calibration.noise_std,
        visibility=visibility,
        rng=rng,
    )
    residual = conditioned_log_enrichment(
        noisy,
        layout,
        alpha=master["selected_method"]["dirichlet_alpha"],
        clip=master["selected_method"]["log_enrichment_clip"],
    )
    scores = score_conditioned_pairs(
        public,
        pairs,
        cells,
        residual,
        layout,
        weight=master["selected_method"]["residual_weight"],
    )
    return scores, time.perf_counter() - started


def method_systems(*, clients, dimension, wall_time, visibility):
    payload = (
        logical_payload_bytes(clients=clients, dimension=dimension)
        if dimension
        else {"client_payload_bytes": 0, "server_release_bytes": 0}
    )
    return {
        "release_dimension": dimension,
        **payload,
        "wall_time_seconds": wall_time,
        "visibility": visibility,
        "cryptographic_overhead_included": False,
    }


def run_dataset(dataset, master, config, calibrations, commit):
    graph = load_p3_graph(RAW, dataset)
    local_dir = PROCESSED / dataset
    with np.load(local_dir / "public_layout.npz", allow_pickle=False) as source:
        homes, cells = source["homes"], source["cells"]
    layout_times = {}
    layouts = {}
    for bin_name, edges in config["binning"].items():
        started = time.perf_counter()
        layouts[bin_name] = public_capacity_layout(
            graph.public_features,
            cells,
            np.asarray(edges),
            maximum_pairs=master["selected_method"][
                "public_capacity_sample_maximum"
            ],
            seed=master["selected_method"]["public_capacity_seed"],
            dirichlet_alpha=master["selected_method"]["dirichlet_alpha"],
        )
        layout_times[bin_name] = time.perf_counter() - started
    records = []
    streams = config["random_streams"]
    for seed in master["split"]["seeds"]:
        with np.load(
            local_dir / f"seed_{seed}_development.npz", allow_pickle=False
        ) as source:
            train_positive = source["train_positive"]
            positive = source["validation_positive"]
            negative = source["validation_negative"]
        pairs, labels = candidate_arrays(positive, negative)
        masks = metric_masks(pairs, homes)
        public_started = time.perf_counter()
        public = sparse_cosine_scores(graph.public_features, pairs)
        public_time = time.perf_counter() - public_started
        train_scores = sparse_cosine_scores(graph.public_features, train_positive)
        local = {
            name: local_count_vectors(
                train_positive,
                train_scores,
                homes,
                cells,
                layout,
                master["clients"],
            )
            for name, layout in layouts.items()
        }
        empty_b8 = tuple(np.zeros(layouts["b8"].dimension) for _ in local["b8"])
        nonprivate_started = time.perf_counter()
        nonprivate_counts = np.sum(np.stack(local["b8"]), axis=0)
        nonprivate_residual = conditioned_log_enrichment(
            nonprivate_counts,
            layouts["b8"],
            alpha=master["selected_method"]["dirichlet_alpha"],
            clip=master["selected_method"]["log_enrichment_clip"],
        )
        nonprivate = score_conditioned_pairs(
            public,
            pairs,
            cells,
            nonprivate_residual,
            layouts["b8"],
            weight=master["selected_method"]["residual_weight"],
        )
        nonprivate_time = time.perf_counter() - nonprivate_started
        random_started = time.perf_counter()
        random = np.random.default_rng(
            np.random.SeedSequence([seed, streams["random_score"]])
        ).random(len(pairs))
        random_time = time.perf_counter() - random_started

        for epsilon_index, epsilon in enumerate(master["privacy"]["epsilon_grid"]):
            calibration = calibrations[float(epsilon)]
            score_map = {
                "public_cosine": public,
                "random_score": random,
                "nonprivate_conditioned_b8_reference": nonprivate,
            }
            systems = {
                "public_cosine": method_systems(
                    clients=master["clients"],
                    dimension=0,
                    wall_time=public_time,
                    visibility="public_only",
                ),
                "random_score": method_systems(
                    clients=master["clients"],
                    dimension=0,
                    wall_time=random_time,
                    visibility="public_only",
                ),
                "nonprivate_conditioned_b8_reference": method_systems(
                    clients=master["clients"],
                    dimension=layouts["b8"].dimension,
                    wall_time=nonprivate_time,
                    visibility="nonprivate_reference",
                ),
            }
            release_specs = (
                (
                    "dp_unconditioned_b1_visible_messages",
                    "b1",
                    local["b1"],
                    "visible_messages",
                    streams["b1_visible"],
                ),
                (
                    "dp_conditioned_b4_visible_messages",
                    "b4",
                    local["b4"],
                    "visible_messages",
                    streams["b4_visible"],
                ),
                (
                    "dp_conditioned_b8_visible_messages",
                    "b8",
                    local["b8"],
                    "visible_messages",
                    streams["b8_visible_and_matched_zero"],
                ),
                (
                    "matched_zero_private_signal_b8_visible",
                    "b8",
                    empty_b8,
                    "visible_messages",
                    streams["b8_visible_and_matched_zero"],
                ),
                (
                    "dp_conditioned_b8_ideal_secagg",
                    "b8",
                    local["b8"],
                    "ideal_secagg",
                    streams["b8_ideal_secagg"],
                ),
            )
            for method, bin_name, counts, visibility, stream in release_specs:
                scores, elapsed = release_and_score(
                    counts,
                    public,
                    pairs,
                    cells,
                    layouts[bin_name],
                    master,
                    calibration=calibration,
                    visibility=visibility,
                    seed=seed,
                    epsilon_index=epsilon_index,
                    stream=stream,
                )
                score_map[method] = scores
                systems[method] = method_systems(
                    clients=master["clients"],
                    dimension=layouts[bin_name].dimension,
                    wall_time=elapsed,
                    visibility=visibility,
                )
            records.append(
                {
                    "protocol": "P3_1_INTERNAL_VALIDATION_v1",
                    "code_commit": commit,
                    "dataset": dataset,
                    "seed": seed,
                    "epsilon_target": epsilon,
                    "split": "validation",
                    "test_accessed": False,
                    "master_config_sha256": sha256(MASTER),
                    "validation_config_sha256": sha256(CONFIG),
                    "source_contract_sha256": sha256(SOURCE_CONTRACT),
                    "split_manifest_sha256": sha256(SPLIT_MANIFEST),
                    "split_audit_sha256": sha256(SPLIT_AUDIT),
                    "privacy": asdict(calibration),
                    "l2_sensitivity": 1.0,
                    "client_count": master["clients"],
                    "client_node_counts": np.bincount(
                        homes, minlength=master["clients"]
                    ).tolist(),
                    "client_train_edge_counts": [
                        int(np.sum(value)) for value in local["b8"]
                    ],
                    "candidate_pair_counts": {
                        name: int(np.sum(mask)) for name, mask in masks.items()
                    },
                    "capacity_layout_seconds": layout_times,
                    "peak_resident_memory_bytes": peak_resident_memory_bytes(),
                    "systems": systems,
                    "metrics": {
                        method: ranking_metrics(labels, scores, masks)
                        for method, scores in score_map.items()
                    },
                }
            )
    return records


def summarize(records, master, config):
    methods = config["methods_per_epsilon"]
    aggregates = {}
    paired = {}
    for dataset in master["datasets"]:
        for epsilon in master["privacy"]["epsilon_grid"]:
            subset = [
                record
                for record in records
                if record["dataset"] == dataset
                and record["epsilon_target"] == epsilon
            ]
            for method in methods:
                for scope in ("global", "intra", "cross"):
                    for metric in ("roc_auc", "average_precision"):
                        values = np.asarray(
                            [record["metrics"][method][scope][metric] for record in subset]
                        )
                        aggregates[
                            f"{dataset}/eps_{epsilon:g}/{method}/{scope}/{metric}"
                        ] = {
                            "n": len(values),
                            "mean": float(np.mean(values)),
                            "std": float(np.std(values, ddof=1)),
                        }
            for scope in ("global", "cross"):
                candidate = np.asarray(
                    [
                        record["metrics"]["dp_conditioned_b8_visible_messages"][scope][
                            "roc_auc"
                        ]
                        for record in subset
                    ]
                )
                public = np.asarray(
                    [record["metrics"]["public_cosine"][scope]["roc_auc"] for record in subset]
                )
                paired[f"{dataset}/eps_{epsilon:g}/{scope}/vs_public"] = paired_summary(
                    candidate, public
                )
    expected = config["operational_pass"]["records"]
    finite_metrics = all(
        np.isfinite(value)
        for record in records
        for method in record["metrics"].values()
        for scope in method.values()
        for value in scope.values()
    )
    checks = {
        "record_count_150": len(records) == expected,
        "all_metrics_finite": finite_metrics,
        "all_methods_present": all(
            set(record["metrics"]) == set(methods) for record in records
        ),
        "sensitivity_one": all(record["l2_sensitivity"] == 1.0 for record in records),
        "test_never_accessed": all(not record["test_accessed"] for record in records),
    }
    return {
        "protocol": "P3_1_INTERNAL_VALIDATION_v1",
        "role": "validation-only internal mechanism audit; selected method unchanged",
        "checks": checks,
        "status": "PASS_TO_EXTERNAL_BASELINE_AUDIT" if all(checks.values()) else "STOP",
        "test_accessed": False,
        "primary_paired_gains": paired,
        "aggregates": aggregates,
    }


def main():
    if OUTPUT.exists():
        raise SystemExit("P3.1 output exists; refusing overwrite")
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("P3 split audit is not clean")
    calibrations = {
        float(epsilon): calibrate_gaussian(
            target_epsilon=epsilon,
            delta=master["privacy"]["delta"],
            sensitivity=master["privacy"]["l2_sensitivity"],
            steps=master["privacy"]["releases_per_run"],
            orders=DEFAULT_ORDERS,
        )
        for epsilon in master["privacy"]["epsilon_grid"]
    }
    commit = git_head()
    records = []
    for dataset in master["datasets"]:
        records.extend(run_dataset(dataset, master, config, calibrations, commit))
    OUTPUT.mkdir(parents=True)
    with (OUTPUT / "records.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    (OUTPUT / "summary.json").write_text(
        json.dumps(summarize(records, master, config), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
