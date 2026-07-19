"""Operationally validate the fixed P2.2 candidate without tuning it."""

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
from fed_dp_lp.p2_data import load_deezer_europe, load_github_social
from fed_dp_lp.p2_pilot import (
    candidate_arrays,
    evaluate_scores,
    metric_masks,
    sparse_cosine_scores,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "p2_2_confirmatory.json"
SOURCE_AUDIT = ROOT / "data" / "manifests" / "p2_2_source_audit.json"
SPLIT_MANIFEST = ROOT / "data" / "manifests" / "p2_2_split_manifest.json"
SPLIT_AUDIT = ROOT / "data" / "manifests" / "p2_2_split_audit.json"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "p2_2_confirmatory"
OUTPUT = ROOT / "results" / "p2_2_confirmatory_validation"
CANDIDATE = "conditioned_b8_lambda_0.1"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def load_graph(dataset: str):
    archive = RAW / dataset / f"{dataset}.zip"
    if dataset == "github-social-snap":
        return load_github_social(archive)
    if dataset == "deezer-europe-snap":
        return load_deezer_europe(archive)
    raise ValueError(dataset)


def local_counts(train_positive, train_scores, homes, cells, layout, clients):
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


def released_scores(local, public, pairs, cells, layout, config, calibration, seed, stream):
    rng = np.random.default_rng(np.random.SeedSequence([seed, stream]))
    noisy = release_conditioned_counts(
        local,
        noise_std=calibration.noise_std,
        visibility="visible_messages",
        rng=rng,
    )
    residual = conditioned_log_enrichment(
        noisy,
        layout,
        alpha=config["candidate"]["dirichlet_alpha"],
        clip=config["candidate"]["log_enrichment_clip"],
    )
    return score_conditioned_pairs(
        public,
        pairs,
        cells,
        residual,
        layout,
        weight=config["candidate"]["residual_weight"],
    )


def run_dataset(dataset: str, config: dict, calibration, commit: str) -> list[dict]:
    graph = load_graph(dataset)
    local_dir = PROCESSED / dataset
    with np.load(local_dir / "public_layout.npz", allow_pickle=False) as source:
        homes, cells = source["homes"], source["cells"]
    layout = public_capacity_layout(
        graph.public_features,
        cells,
        np.asarray(config["candidate"]["bin_edges"]),
        maximum_pairs=config["candidate"]["public_capacity_sample_maximum"],
        seed=config["candidate"]["public_capacity_seed"],
        dirichlet_alpha=config["candidate"]["dirichlet_alpha"],
    )
    records = []
    for seed in config["split"]["seeds"]:
        with np.load(
            local_dir / f"seed_{seed}_development.npz", allow_pickle=False
        ) as source:
            train_positive = source["train_positive"]
            positive = source["validation_positive"]
            negative = source["validation_negative"]
        pairs, labels = candidate_arrays(positive, negative)
        masks = metric_masks(pairs, homes)
        public = sparse_cosine_scores(graph.public_features, pairs)
        train_scores = sparse_cosine_scores(graph.public_features, train_positive)
        local = local_counts(
            train_positive,
            train_scores,
            homes,
            cells,
            layout,
            config["clients"],
        )
        empty = tuple(np.zeros(layout.dimension) for _ in local)
        rng = np.random.default_rng(np.random.SeedSequence([seed, 5201]))
        methods = {
            "public_cosine": public,
            "random_score": rng.random(len(pairs)),
            "zero_private_signal": released_scores(
                empty, public, pairs, cells, layout, config, calibration, seed, 5301
            ),
            CANDIDATE: released_scores(
                local, public, pairs, cells, layout, config, calibration, seed, 5401
            ),
        }
        records.append(
            {
                "protocol": "P2_2_CONFIRMATORY_VALIDATION_v1",
                "code_commit": commit,
                "dataset": dataset,
                "seed": seed,
                "split": "validation",
                "test_accessed": False,
                "config_sha256": sha256(CONFIG),
                "source_audit_sha256": sha256(SOURCE_AUDIT),
                "split_manifest_sha256": sha256(SPLIT_MANIFEST),
                "split_audit_sha256": sha256(SPLIT_AUDIT),
                "privacy": asdict(calibration),
                "release_dimension": layout.dimension,
                "l2_sensitivity": 1.0,
                "client_count": config["clients"],
                "client_node_counts": np.bincount(
                    homes, minlength=config["clients"]
                ).tolist(),
                "client_train_edge_counts": [int(np.sum(value)) for value in local],
                "candidate_pair_counts": {
                    name: int(np.sum(mask)) for name, mask in masks.items()
                },
                "metrics": {
                    name: evaluate_scores(labels, scores, masks)
                    for name, scores in methods.items()
                },
            }
        )
    return records


def summarize(records: list[dict], config: dict) -> dict:
    cells = {}
    for dataset in config["datasets"]:
        subset = [record for record in records if record["dataset"] == dataset]
        for metric in ("global", "cross"):
            candidate = np.asarray(
                [record["metrics"][CANDIDATE][metric] for record in subset]
            )
            for reference_name in ("public_cosine", "zero_private_signal", "random_score"):
                reference = np.asarray(
                    [record["metrics"][reference_name][metric] for record in subset]
                )
                summary = paired_summary(candidate, reference)
                summary["candidate_mean"] = float(np.mean(candidate))
                summary["reference_mean"] = float(np.mean(reference))
                cells[f"{dataset}/{metric}/vs_{reference_name}"] = summary
    checks = {
        "all_ten_records_present": len(records) == 10,
        "fixed_candidate_only": all(
            set(record["metrics"])
            == {"public_cosine", "random_score", "zero_private_signal", CANDIDATE}
            for record in records
        ),
        "release_dimension_1088": all(
            record["release_dimension"] == 1088 for record in records
        ),
        "sensitivity_one": all(record["l2_sensitivity"] == 1.0 for record in records),
        "test_never_accessed": all(not record["test_accessed"] for record in records),
    }
    return {
        "protocol": "P2_2_CONFIRMATORY_VALIDATION_v1",
        "candidate": CANDIDATE,
        "role": "operational validation only; no tuning or utility gate",
        "checks": checks,
        "status": "READY_FOR_TEST_RUNNER_FREEZE" if all(checks.values()) else "STOP",
        "test_accessed": False,
        "paired_diagnostics": cells,
    }


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("P2.2 validation output exists; refusing overwrite")
    split_audit = json.loads(SPLIT_AUDIT.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("refusing validation after failed/nonsealed split audit")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
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
        records.extend(run_dataset(dataset, config, calibration, commit))
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
