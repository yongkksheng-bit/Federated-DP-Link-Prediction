"""Decrypt and evaluate the frozen fresh-source frontier test exactly once."""

from __future__ import annotations

import hashlib
import io
import json
import pathlib
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone

import numpy as np
from cryptography.fernet import Fernet
from scipy.stats import spearmanr

from fed_dp_lp.accounting import DEFAULT_ORDERS, calibrate_gaussian
from fed_dp_lp.frontier import (
    degree_upper_energy_ratio,
    exact_spearman_permutation_pvalue,
    expected_noise_energy,
    gaussian_norm_interval,
    signal_noise_energy_ratio,
)
from fed_dp_lp.gap_adaptation import (
    UNDIRECTED_EDGE_L2_SENSITIVITY,
    client_owned_edges,
    normalize_rows,
    release_private_aggregations,
    score_pairs_from_channels,
    undirected_adjacency,
)
from fed_dp_lp.metrics import roc_auc
from fed_dp_lp.p2_pilot import candidate_arrays, metric_masks
from fed_dp_lp.p2_sealing import array_commitment
from fed_dp_lp.p5fc_data import (
    cached_dense_public_svd_encoder,
    dense_cosine_scores,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p5fc_fresh_frontier.json"
SOURCE_AUDIT_PATH = ROOT / "data/manifests/p5fc_source_audit.json"
SOURCE_MANIFEST_PATH = ROOT / "data/manifests/p5fc_sources.json"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p5fc_split_manifest.json"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p5fc_split_audit.json"
RAW = ROOT / "data/raw/p5fc"
PROCESSED = ROOT / "data/processed/p5fc_frontier"
SEALED = ROOT / "data/sealed/p5fc_frontier"
CACHE = ROOT / "data/cache/p5fc_frontier"
OUTPUT = ROOT / "results/p5fc_frontier_test"
ACCESS = OUTPUT / "access.json"


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


def require_clean_worktree() -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True
    ).strip()
    if status:
        raise SystemExit("refusing one-time test from a dirty worktree")


def unseal(
    dataset: str,
    seed: int,
    manifest_record: dict,
    cipher: Fernet,
    commitment_key: bytes,
) -> tuple[np.ndarray, np.ndarray]:
    path = SEALED / f"{dataset}_seed_{seed}.fernet"
    if sha256(path) != manifest_record["commitments"]["sealed_payload_sha256"]:
        raise RuntimeError("sealed payload hash mismatch")
    plaintext = cipher.decrypt(path.read_bytes())
    with np.load(io.BytesIO(plaintext), allow_pickle=False) as payload:
        positive = payload["test_positive"]
        negative = payload["test_negative"]
    for name, values in (("test_positive", positive), ("test_negative", negative)):
        observed = array_commitment(
            commitment_key, f"{dataset}|{seed}|{name}", values
        )
        if observed != manifest_record["commitments"][name]:
            raise RuntimeError(f"{name} commitment mismatch")
    return positive, negative


def scoped_auc(labels: np.ndarray, scores: np.ndarray, masks: dict) -> dict:
    return {
        scope: roc_auc(labels[mask], scores[mask])
        for scope, mask in masks.items()
    }


def write_jsonl(path: pathlib.Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> None:
    require_clean_worktree()
    if OUTPUT.exists():
        raise SystemExit("P5FC test output/access state exists; refusing rerun")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    source_audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    split_manifest = json.loads(SPLIT_MANIFEST_PATH.read_text(encoding="utf-8"))
    if source_audit["status"] != "PASS" or split_audit["status"] != "PASS":
        raise SystemExit("source/split audits must pass before test access")
    if (
        split_manifest["test_status"] != "encrypted_never_accessed"
        or split_manifest["test_access_count"] != 0
    ):
        raise SystemExit("fresh test payload is not untouched")

    commit = git_head()
    OUTPUT.mkdir(parents=True)
    access = {
        "protocol": config["protocol"],
        "accessed_utc": datetime.now(timezone.utc).isoformat(),
        "test_access_count": 1,
        "runner_commit": commit,
        "config_sha256": sha256(CONFIG_PATH),
        "source_audit_sha256": sha256(SOURCE_AUDIT_PATH),
        "split_manifest_sha256": sha256(SPLIT_MANIFEST_PATH),
        "split_audit_sha256": sha256(SPLIT_AUDIT_PATH),
    }
    ACCESS.write_text(json.dumps(access, indent=2) + "\n", encoding="utf-8")

    cipher = Fernet((SEALED / "test.key").read_bytes())
    commitment_key = (SEALED / "commitment.key").read_bytes()
    split_records = {
        (dataset["dataset"], record["seed"]): record
        for dataset in split_manifest["datasets"] for record in dataset["splits"]
    }
    records = []
    requested_dimension = config["public_encoder"]["requested_dimension"]
    random_state = config["public_encoder"]["random_state"]
    hops = config["release"]["hops"]

    for dataset_index, dataset in enumerate(config["datasets"]):
        print(f"[{dataset}] preparing frozen public encoder", flush=True)
        feature_path = RAW / dataset / "feats.npy"
        encoding_cache = CACHE / f"{dataset}_d{requested_dimension}_s{random_state}.npz"
        normalized_cache = CACHE / f"{dataset}_row_normalized.npy"
        encoded = cached_dense_public_svd_encoder(
            feature_path,
            dimension=requested_dimension,
            random_state=random_state,
            normalized_cache_path=normalized_cache,
            encoding_cache_path=encoding_cache,
        )
        with np.load(PROCESSED / dataset / "public_layout.npz") as source:
            homes = source["homes"]
        for seed in config["split"]["seeds"]:
            print(f"[{dataset}] test seed={seed}", flush=True)
            development_path = PROCESSED / dataset / f"seed_{seed}_development.npz"
            development_hash = sha256(development_path)
            with np.load(development_path, allow_pickle=False) as source:
                train_positive = source["train_positive"]
            test_positive, test_negative = unseal(
                dataset,
                seed,
                split_records[(dataset, seed)],
                cipher,
                commitment_key,
            )
            pairs, labels = candidate_arrays(test_positive, test_negative)
            masks = metric_masks(pairs, homes)
            public_scores = dense_cosine_scores(feature_path, pairs)
            public_auc = scoped_auc(labels, public_scores, masks)
            local_edges = client_owned_edges(
                train_positive, homes, clients=config["clients"]
            )
            adjacency = undirected_adjacency(local_edges, len(homes))
            first_signal = adjacency @ normalize_rows(encoded)
            degrees = np.asarray(adjacency.sum(axis=1)).ravel()
            for epsilon_index, epsilon in enumerate(
                config["privacy"]["epsilon_grid"]
            ):
                calibration = calibrate_gaussian(
                    target_epsilon=epsilon,
                    delta=config["privacy"]["delta"],
                    sensitivity=UNDIRECTED_EDGE_L2_SENSITIVITY,
                    steps=hops,
                    orders=DEFAULT_ORDERS,
                )
                for visibility in config["privacy"]["visibility_models"]:
                    rng = np.random.default_rng(np.random.SeedSequence([
                        config["rng_streams"][visibility],
                        dataset_index,
                        seed,
                        epsilon_index,
                        requested_dimension,
                        hops,
                    ]))
                    channels = release_private_aggregations(
                        local_edges,
                        encoded,
                        hops=hops,
                        noise_std=calibration.noise_std,
                        visibility=visibility,
                        rng=rng,
                        adjacency=adjacency,
                    )
                    private_scores = score_pairs_from_channels(channels, pairs)
                    private_auc = scoped_auc(labels, private_scores, masks)
                    release_dimension = len(homes) * encoded.shape[1]
                    lower, upper = gaussian_norm_interval(
                        release_dimension=release_dimension,
                        noise_std=calibration.noise_std,
                        clients=config["clients"],
                        visibility=visibility,
                        failure_probability=0.05,
                    )
                    records.append({
                        "protocol": config["protocol"],
                        "code_commit": commit,
                        "dataset": dataset,
                        "seed": seed,
                        "epsilon_target": epsilon,
                        "visibility": visibility,
                        "split": "fresh_confirmatory_test",
                        "test_access_count": 1,
                        "config_sha256": sha256(CONFIG_PATH),
                        "source_audit_sha256": sha256(SOURCE_AUDIT_PATH),
                        "split_manifest_sha256": sha256(SPLIT_MANIFEST_PATH),
                        "split_audit_sha256": sha256(SPLIT_AUDIT_PATH),
                        "development_file_sha256": development_hash,
                        "public_encoding_cache": str(encoding_cache.relative_to(ROOT)),
                        "public_encoding_cache_sha256": sha256(encoding_cache),
                        "privacy": asdict(calibration),
                        "l2_sensitivity_per_release": UNDIRECTED_EDGE_L2_SENSITIVITY,
                        "release_count": hops,
                        "client_count": config["clients"],
                        "projection_dimension": encoded.shape[1],
                        "first_hop_release_dimension": release_dimension,
                        "first_hop_signal_frobenius_squared": float(
                            np.linalg.norm(first_signal) ** 2
                        ),
                        "degree_squared_sum": float(np.sum(degrees**2)),
                        "expected_first_hop_noise_energy": expected_noise_energy(
                            release_dimension=release_dimension,
                            noise_std=calibration.noise_std,
                            clients=config["clients"],
                            visibility=visibility,
                        ),
                        "frontier_signal_ratio": signal_noise_energy_ratio(
                            first_signal,
                            noise_std=calibration.noise_std,
                            clients=config["clients"],
                            visibility=visibility,
                        ),
                        "frontier_degree_upper_ratio": degree_upper_energy_ratio(
                            degrees,
                            encoding_dimension=encoded.shape[1],
                            noise_std=calibration.noise_std,
                            clients=config["clients"],
                            visibility=visibility,
                        ),
                        "noise_norm_interval_95": [lower, upper],
                        "metrics": {
                            "gap_style": private_auc,
                            "public_cosine": public_auc,
                            "gain_over_public": {
                                scope: private_auc[scope] - public_auc[scope]
                                for scope in ("global", "intra", "cross")
                            },
                        },
                    })

    cells = []
    for dataset in config["datasets"]:
        for epsilon in config["privacy"]["epsilon_grid"]:
            for visibility in config["privacy"]["visibility_models"]:
                subset = [
                    record for record in records
                    if record["dataset"] == dataset
                    and record["epsilon_target"] == epsilon
                    and record["visibility"] == visibility
                ]
                cells.append({
                    "dataset": dataset,
                    "epsilon": epsilon,
                    "visibility": visibility,
                    "seeds": len(subset),
                    "mean_log10_frontier_signal_ratio": float(np.mean([
                        np.log10(record["frontier_signal_ratio"])
                        for record in subset
                    ])),
                    "mean_global_auc_gain": float(np.mean([
                        record["metrics"]["gain_over_public"]["global"]
                        for record in subset
                    ])),
                    "mean_cross_auc_gain": float(np.mean([
                        record["metrics"]["gain_over_public"]["cross"]
                        for record in subset
                    ])),
                })

    pooled_rho = float(spearmanr(
        [cell["mean_log10_frontier_signal_ratio"] for cell in cells],
        [cell["mean_global_auc_gain"] for cell in cells],
    ).statistic)
    per_dataset = {}
    for dataset in config["datasets"]:
        subset = [cell for cell in cells if cell["dataset"] == dataset]
        rho, pvalue = exact_spearman_permutation_pvalue(
            np.asarray([cell["mean_log10_frontier_signal_ratio"] for cell in subset]),
            np.asarray([cell["mean_global_auc_gain"] for cell in subset]),
        )
        per_dataset[dataset] = {
            "cells": len(subset),
            "spearman": rho,
            "exact_two_sided_permutation_pvalue": pvalue,
        }

    energy_pairs = {}
    for record in records:
        key = (record["dataset"], record["seed"], record["epsilon_target"])
        energy_pairs.setdefault(key, {})[record["visibility"]] = record[
            "expected_first_hop_noise_energy"
        ]
    gate = config["confirmatory_gate"]
    checks = {
        "records_complete": len(records) == gate["expected_records"],
        "cells_complete": len(cells) == gate["expected_aggregate_cells"]
        and all(cell["seeds"] == len(config["split"]["seeds"]) for cell in cells),
        "pooled_spearman": pooled_rho >= gate["minimum_pooled_cell_spearman"],
        "each_dataset_spearman": all(
            item["spearman"] >= gate["minimum_each_dataset_cell_spearman"]
            for item in per_dataset.values()
        ),
        "each_dataset_exact_pvalue": all(
            item["exact_two_sided_permutation_pvalue"]
            <= gate["maximum_each_dataset_exact_permutation_pvalue"]
            for item in per_dataset.values()
        ),
        "noise_energy_ratio": all(
            set(pair) == set(config["privacy"]["visibility_models"])
            and np.isclose(
                pair["visible_messages"] / pair["ideal_secagg"],
                gate["required_noise_energy_ratio_visible_over_ideal"],
            )
            for pair in energy_pairs.values()
        ),
        "degree_bound": all(
            record["frontier_signal_ratio"]
            <= record["frontier_degree_upper_ratio"] + 1e-12
            for record in records
        ),
        "finite": all(
            np.isfinite([
                record["frontier_signal_ratio"],
                record["frontier_degree_upper_ratio"],
                *record["metrics"]["gap_style"].values(),
                *record["metrics"]["public_cosine"].values(),
                *record["metrics"]["gain_over_public"].values(),
            ]).all()
            for record in records
        ),
        "single_test_access": all(record["test_access_count"] == 1 for record in records),
    }
    decision = (
        "CONFIRM_GENERAL_FRONTIER_DIAGNOSTIC"
        if all(checks.values())
        else "REJECT_GENERAL_FRONTIER_CLAIM"
    )
    write_jsonl(OUTPUT / "records.jsonl", records)
    write_jsonl(OUTPUT / "cells.jsonl", cells)
    (OUTPUT / "summary.json").write_text(json.dumps({
        "protocol": config["protocol"],
        "record_count": len(records),
        "cell_count": len(cells),
        "pooled_cell_spearman": pooled_rho,
        "per_dataset": per_dataset,
        "checks": checks,
        "decision": decision,
        "test_access_count": 1,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
