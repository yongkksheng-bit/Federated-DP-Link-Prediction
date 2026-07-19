"""Evaluation helpers for the preregistered P2 coarsened-release pilot."""

from __future__ import annotations

import numpy as np
from scipy import sparse
from sklearn.preprocessing import normalize

from .metrics import roc_auc


def candidate_arrays(
    positive: np.ndarray, negative: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    pairs = np.concatenate([positive, negative], axis=0)
    labels = np.concatenate(
        [np.ones(len(positive), dtype=np.int64), np.zeros(len(negative), dtype=np.int64)]
    )
    return pairs, labels


def metric_masks(pairs: np.ndarray, homes: np.ndarray) -> dict[str, np.ndarray]:
    cross = homes[pairs[:, 0]] != homes[pairs[:, 1]]
    return {
        "global": np.ones(len(pairs), dtype=bool),
        "intra": ~cross,
        "cross": cross,
    }


def evaluate_scores(
    labels: np.ndarray, scores: np.ndarray, masks: dict[str, np.ndarray]
) -> dict[str, float]:
    return {
        name: roc_auc(labels[mask], scores[mask])
        for name, mask in masks.items()
    }


def sparse_cosine_scores(features: sparse.csr_matrix, pairs: np.ndarray) -> np.ndarray:
    normalized = normalize(features, norm="l2", axis=1, copy=True)
    products = normalized[pairs[:, 0]].multiply(normalized[pairs[:, 1]])
    return np.asarray(products.sum(axis=1)).ravel()
