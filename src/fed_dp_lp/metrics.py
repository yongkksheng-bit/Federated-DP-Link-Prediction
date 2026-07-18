"""Ranking metrics and paired uncertainty summaries."""

from __future__ import annotations

import numpy as np
from scipy.stats import rankdata, t


def roc_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=np.int64)
    scores = np.asarray(scores, dtype=np.float64)
    if labels.shape != scores.shape:
        raise ValueError("labels and scores must have identical shapes")
    positive = labels == 1
    negative = labels == 0
    n_pos = int(np.sum(positive))
    n_neg = int(np.sum(negative))
    if n_pos == 0 or n_neg == 0:
        raise ValueError("ROC-AUC requires both positive and negative examples")
    ranks = rankdata(scores, method="average")
    return float((np.sum(ranks[positive]) - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def paired_summary(values: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    reference = np.asarray(reference, dtype=np.float64)
    if values.shape != reference.shape or values.ndim != 1 or values.size < 2:
        raise ValueError("paired vectors must share shape and contain at least two values")
    differences = values - reference
    mean = float(np.mean(differences))
    standard_error = float(np.std(differences, ddof=1) / np.sqrt(differences.size))
    half_width = float(t.ppf(0.975, differences.size - 1) * standard_error)
    return {
        "n": int(differences.size),
        "mean_difference": mean,
        "ci95_low": mean - half_width,
        "ci95_high": mean + half_width,
    }
