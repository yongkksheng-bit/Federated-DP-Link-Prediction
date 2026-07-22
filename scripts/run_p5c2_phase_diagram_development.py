"""Develop the frozen two-axis phase diagram without any test access."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

import numpy as np

from fed_dp_lp.gap_adaptation import (
    cached_public_svd_encoder,
    normalize_rows,
    undirected_adjacency,
)
from fed_dp_lp.metrics import roc_auc
from fed_dp_lp.p2_pilot import candidate_arrays, metric_masks, sparse_cosine_scores
from fed_dp_lp.p3_data import load_p3_graph
from fed_dp_lp.phase_diagram import (
    leave_one_dataset_out_predictions,
    normalized_effective_rank,
    prediction_metrics,
    select_stratified_probe,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/p5c2_phase_diagram_development.json"
MASTER_PATH = ROOT / "configs/p3_master_benchmark.json"
P5F_CONFIG_PATH = ROOT / "configs/p5f_frontier_validation.json"
P5F_RECORDS_PATH = ROOT / "results/p5f_frontier_validation/records.jsonl"
SPLIT_AUDIT_PATH = ROOT / "data/manifests/p3_split_audit.json"
SPLIT_MANIFEST_PATH = ROOT / "data/manifests/p3_split_manifest.json"
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed/p3_benchmark"
CACHE = ROOT / "data/cache/public_svd"
OUTPUT = ROOT / "results/p5c2_phase_diagram_development"


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
    if OUTPUT.exists():
        raise SystemExit("P5C2 output exists; refusing overwrite")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    p5f_config = json.loads(P5F_CONFIG_PATH.read_text(encoding="utf-8"))
    split_audit = json.loads(SPLIT_AUDIT_PATH.read_text(encoding="utf-8"))
    if split_audit["status"] != "PASS" or split_audit["test_decrypted"]:
        raise SystemExit("P3 split audit is not clean")
    if config["datasets"] != master["datasets"]:
        raise SystemExit("C2 datasets differ from frozen P3 development domains")
    p5f_records = [
        json.loads(line) for line in P5F_RECORDS_PATH.read_text().splitlines()
    ]
    if any(record["test_accessed"] or record["split"] != "validation" for record in p5f_records):
        raise SystemExit("P5F input contains non-validation evidence")

    commit = git_head()
    proxy_records = []
    proxy_config = config["cross_fitted_alignment_axis"]
    for dataset in config["datasets"]:
        print(f"[{dataset}] C2 proxy start", flush=True)
        graph = load_p3_graph(RAW, dataset)
        backbone = p5f_config["frozen_gap_backbones"][dataset]
        dimension = backbone["projection_dimension"]
        cache_path = CACHE / f"{dataset}_d{dimension}_s{20260724 + dimension}.npz"
        encoded = cached_public_svd_encoder(
            graph.public_features,
            dimension=dimension,
            random_state=20260724 + dimension,
            cache_path=cache_path,
        )
        with np.load(PROCESSED / dataset / "public_layout.npz") as source:
            homes = source["homes"]
        for seed in config["seeds"]:
            development_path = PROCESSED / dataset / f"seed_{seed}_development.npz"
            with np.load(development_path, allow_pickle=False) as source:
                train_positive = source["train_positive"]
                train_negative = source["train_negative"]
            fit_positive, probe_positive = select_stratified_probe(
                train_positive,
                homes,
                fraction=proxy_config["probe_positive_fraction"],
                cap=proxy_config["probe_positive_cap"],
                seed=seed + proxy_config["rank_seed_offset"],
            )
            _, probe_negative = select_stratified_probe(
                train_negative,
                homes,
                fraction=proxy_config["probe_positive_fraction"],
                cap=proxy_config["probe_positive_cap"],
                seed=seed + proxy_config["rank_seed_offset"] + 1,
            )
            pairs, labels = candidate_arrays(probe_positive, probe_negative)
            masks = metric_masks(pairs, homes)
            public_scores = sparse_cosine_scores(graph.public_features, pairs)
            adjacency = undirected_adjacency((fit_positive,), len(homes))
            structural = normalize_rows(adjacency @ normalize_rows(encoded))
            structural_scores = np.einsum(
                "ij,ij->i",
                structural[pairs[:, 0]],
                structural[pairs[:, 1]],
            )
            fusion_scores = 0.5 * (public_scores + structural_scores)
            public_auc = scoped_auc(labels, public_scores, masks)
            structural_auc = scoped_auc(labels, structural_scores, masks)
            fusion_auc = scoped_auc(labels, fusion_scores, masks)
            positive = labels == 1
            public_margin = float(
                public_scores[positive].mean() - public_scores[~positive].mean()
            )
            fusion_margin = float(
                fusion_scores[positive].mean() - fusion_scores[~positive].mean()
            )
            degrees = np.asarray(adjacency.sum(axis=1)).ravel()
            proxy_records.append({
                "protocol": config["protocol"],
                "code_commit": commit,
                "dataset": dataset,
                "seed": seed,
                "split": "training_internal_cross_fit",
                "test_accessed": False,
                "config_sha256": sha256(CONFIG_PATH),
                "master_config_sha256": sha256(MASTER_PATH),
                "p5f_config_sha256": sha256(P5F_CONFIG_PATH),
                "p5f_records_sha256": sha256(P5F_RECORDS_PATH),
                "p3_split_manifest_sha256": sha256(SPLIT_MANIFEST_PATH),
                "development_file_sha256": sha256(development_path),
                "public_encoding_cache": str(cache_path.relative_to(ROOT)),
                "public_encoding_cache_sha256": sha256(cache_path),
                "requested_dimension": dimension,
                "actual_dimension": encoded.shape[1],
                "fit_positive_count": len(fit_positive),
                "probe_positive_count": len(probe_positive),
                "probe_negative_count": len(probe_negative),
                "metrics": {
                    "public_auc": public_auc,
                    "clean_structural_auc": structural_auc,
                    "clean_fusion_auc": fusion_auc,
                    "clean_fusion_gain_cv": {
                        scope: fusion_auc[scope] - public_auc[scope]
                        for scope in ("global", "intra", "cross")
                    },
                    "clean_structural_gain_cv": {
                        scope: structural_auc[scope] - public_auc[scope]
                        for scope in ("global", "intra", "cross")
                    },
                    "clean_fusion_margin_gain_cv": fusion_margin - public_margin,
                    "normalized_structural_effective_rank": normalized_effective_rank(
                        structural
                    ),
                    "training_degree_coefficient_of_variation": float(
                        degrees.std() / max(degrees.mean(), np.finfo(float).tiny)
                    ),
                },
            })
        print(f"[{dataset}] C2 proxy complete", flush=True)

    cells = []
    for dataset in config["datasets"]:
        alignment = float(np.mean([
            record["metrics"]["clean_fusion_gain_cv"]["global"]
            for record in proxy_records if record["dataset"] == dataset
        ]))
        for epsilon in p5f_config["epsilon_grid"]:
            for visibility in p5f_config["visibility_models"]:
                subset = [
                    record for record in p5f_records
                    if record["dataset"] == dataset
                    and record["epsilon_target"] == epsilon
                    and record["visibility"] == visibility
                ]
                recoverability = float(np.mean([
                    record["frontier_signal_ratio"]
                    / (1.0 + record["frontier_signal_ratio"])
                    for record in subset
                ]))
                cells.append({
                    "dataset": dataset,
                    "epsilon": epsilon,
                    "visibility": visibility,
                    "seeds": len(subset),
                    "energy_recoverability": recoverability,
                    "alignment_clean_fusion_gain_cv": alignment,
                    "outcome_global_auc_gain": float(np.mean([
                        record["metrics"]["gain_over_public"]["global"]
                        for record in subset
                    ])),
                })

    datasets = np.asarray([cell["dataset"] for cell in cells])
    recoverability = np.asarray([cell["energy_recoverability"] for cell in cells])
    alignment = np.asarray([
        cell["alignment_clean_fusion_gain_cv"] for cell in cells
    ])
    outcome = np.asarray([cell["outcome_global_auc_gain"] for cell in cells])
    one_axis = np.column_stack([recoverability, recoverability**2])
    two_axis = np.column_stack([
        recoverability,
        recoverability**2,
        alignment,
        recoverability * alignment,
    ])
    ridge = config["phase_model"]["ridge"]
    one_predictions = leave_one_dataset_out_predictions(
        datasets, one_axis, outcome, ridge=ridge
    )
    two_predictions = leave_one_dataset_out_predictions(
        datasets, two_axis, outcome, ridge=ridge
    )
    one_metrics = prediction_metrics(outcome, one_predictions)
    two_metrics = prediction_metrics(outcome, two_predictions)
    for index, cell in enumerate(cells):
        cell["one_axis_lodo_prediction"] = float(one_predictions[index])
        cell["two_axis_lodo_prediction"] = float(two_predictions[index])

    per_dataset = {}
    for dataset in config["datasets"]:
        mask = datasets == dataset
        one_mae = float(np.mean(np.abs(outcome[mask] - one_predictions[mask])))
        two_mae = float(np.mean(np.abs(outcome[mask] - two_predictions[mask])))
        per_dataset[dataset] = {
            "one_axis_mae": one_mae,
            "two_axis_mae": two_mae,
            "mae_change": two_mae - one_mae,
        }
    relative_reduction = (one_metrics["mae"] - two_metrics["mae"]) / one_metrics["mae"]
    gate = config["go_no_go"]
    checks = {
        "proxy_records_complete": len(proxy_records) == gate["expected_proxy_records"],
        "phase_cells_complete": len(cells) == gate["expected_phase_cells"]
        and all(cell["seeds"] == len(config["seeds"]) for cell in cells),
        "relative_mae_reduction": relative_reduction
        >= gate["minimum_relative_lodo_mae_reduction"],
        "sign_accuracy": two_metrics["sign_accuracy"]
        >= gate["minimum_lodo_sign_accuracy"],
        "prediction_spearman": two_metrics["spearman"]
        >= gate["minimum_lodo_prediction_spearman"],
        "datasets_improved": sum(
            item["two_axis_mae"] < item["one_axis_mae"]
            for item in per_dataset.values()
        ) >= gate["minimum_datasets_with_lower_mae"],
        "worst_dataset_degradation": max(
            item["mae_change"] for item in per_dataset.values()
        ) <= gate["maximum_any_dataset_mae_degradation"],
        "finite": np.isfinite([
            *one_predictions,
            *two_predictions,
            *outcome,
            *alignment,
            *recoverability,
        ]).all(),
        "test_never_accessed": all(
            not record["test_accessed"] for record in proxy_records
        ) and all(not record["test_accessed"] for record in p5f_records),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    decision = (
        "ADVANCE_TWO_AXIS_TO_NEW_SOURCE_CONFIRMATION"
        if all(checks.values())
        else "REJECT_TWO_AXIS_PHASE_PROXY"
    )
    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "proxy_records.jsonl", proxy_records)
    write_jsonl(OUTPUT / "phase_cells.jsonl", cells)
    (OUTPUT / "summary.json").write_text(json.dumps({
        "protocol": config["protocol"],
        "proxy_record_count": len(proxy_records),
        "phase_cell_count": len(cells),
        "one_axis_lodo": one_metrics,
        "two_axis_lodo": two_metrics,
        "relative_mae_reduction": float(relative_reduction),
        "datasets_with_lower_mae": sum(
            item["two_axis_mae"] < item["one_axis_mae"]
            for item in per_dataset.values()
        ),
        "per_dataset": per_dataset,
        "checks": checks,
        "decision": decision,
        "test_accessed": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUTPUT / "summary.json")


if __name__ == "__main__":
    main()
