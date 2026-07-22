"""Cross-fitted alignment and two-axis phase-diagram utilities."""

from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr

from .p5fc_data import edge_keys, splitmix64


def select_stratified_probe(
    pairs: np.ndarray,
    homes: np.ndarray,
    *,
    fraction: float,
    cap: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return retained/probe pairs with a balanced deterministic probe."""
    pairs = np.asarray(pairs, dtype=np.int64)
    homes = np.asarray(homes, dtype=np.int64)
    if not 0 < fraction < 1 or cap < 2:
        raise ValueError("invalid probe fraction or cap")
    total = min(int(np.floor(fraction * len(pairs))), cap)
    total -= total % 2
    if total < 2:
        raise ValueError("probe contains fewer than two pairs")
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    keys = edge_keys(pairs, nodes=len(homes))
    selected = np.zeros(len(pairs), dtype=bool)
    per_stratum = total // 2
    for is_cross in (False, True):
        indices = np.flatnonzero(cross == is_cross)
        if len(indices) < per_stratum:
            raise ValueError("pair stratum is smaller than balanced probe")
        ranks = splitmix64(keys[indices], seed=seed)
        local = np.argpartition(ranks, per_stratum - 1)[:per_stratum]
        chosen = indices[local]
        order = np.lexsort((keys[chosen], ranks[local]))
        selected[chosen[order]] = True
    return pairs[~selected], pairs[selected]


def normalized_effective_rank(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] == 0:
        raise ValueError("values must be a nonempty matrix")
    gram = values.T @ values
    eigenvalues = np.maximum(np.linalg.eigvalsh(gram), 0.0)
    denominator = float(np.sum(eigenvalues**2))
    if denominator == 0:
        return 0.0
    participation = float(np.sum(eigenvalues) ** 2 / denominator)
    return participation / values.shape[1]


def _standardized_design(
    train: np.ndarray, test: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    mean = train.mean(axis=0)
    scale = train.std(axis=0)
    scale[scale == 0] = 1.0
    train_scaled = (train - mean) / scale
    test_scaled = (test - mean) / scale
    return (
        np.column_stack([np.ones(len(train)), train_scaled]),
        np.column_stack([np.ones(len(test)), test_scaled]),
    )


def ridge_fold_predict(
    train_features: np.ndarray,
    train_outcome: np.ndarray,
    test_features: np.ndarray,
    *,
    ridge: float,
) -> np.ndarray:
    train = np.asarray(train_features, dtype=np.float64)
    test = np.asarray(test_features, dtype=np.float64)
    outcome = np.asarray(train_outcome, dtype=np.float64)
    if train.ndim != 2 or test.shape[1] != train.shape[1] or ridge < 0:
        raise ValueError("invalid ridge fold inputs")
    design, test_design = _standardized_design(train, test)
    penalty = np.eye(design.shape[1]) * ridge
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(
        design.T @ design + penalty, design.T @ outcome
    )
    return test_design @ coefficients


def leave_one_dataset_out_predictions(
    datasets: np.ndarray,
    features: np.ndarray,
    outcome: np.ndarray,
    *,
    ridge: float,
) -> np.ndarray:
    datasets = np.asarray(datasets)
    features = np.asarray(features, dtype=np.float64)
    outcome = np.asarray(outcome, dtype=np.float64)
    predictions = np.empty(len(outcome), dtype=np.float64)
    for dataset in np.unique(datasets):
        test = datasets == dataset
        train = ~test
        predictions[test] = ridge_fold_predict(
            features[train], outcome[train], features[test], ridge=ridge
        )
    return predictions


def prediction_metrics(outcome: np.ndarray, predictions: np.ndarray) -> dict:
    outcome = np.asarray(outcome, dtype=np.float64)
    predictions = np.asarray(predictions, dtype=np.float64)
    return {
        "mae": float(np.mean(np.abs(outcome - predictions))),
        "sign_accuracy": float(np.mean(np.signbit(outcome) == np.signbit(predictions))),
        "spearman": float(spearmanr(outcome, predictions).statistic),
    }
