"""Bounded post-processing maps for public-preserving DP residual scores."""

from __future__ import annotations

import numpy as np
from scipy.stats import rankdata

from .block_release import BlockLayout


def residual_map(
    noisy_counts: np.ndarray,
    layout: BlockLayout,
    *,
    transform: str,
) -> np.ndarray:
    noisy_counts = np.asarray(noisy_counts, dtype=np.float64)
    if noisy_counts.shape != (layout.dimension,):
        raise ValueError("noisy counts must match the block layout")
    smoothed = (np.clip(noisy_counts, 0.0, layout.capacities) + 0.5) / (
        layout.capacities + 1.0
    )
    if transform == "centered_block_rank":
        ranks = rankdata(smoothed, method="average") / layout.dimension
        return np.clip(2.0 * ranks - 1.0, -1.0, 1.0)
    if transform == "clipped_log_density_zscore":
        values = np.log(smoothed)
        scale = float(np.std(values))
        if scale == 0:
            return np.zeros_like(values)
        standardized = (values - float(np.mean(values))) / scale
        return np.clip(standardized, -3.0, 3.0) / 3.0
    raise ValueError(f"unknown residual transform: {transform}")


def score_with_residual(
    public_scores: np.ndarray,
    pairs: np.ndarray,
    groups: np.ndarray,
    residuals: np.ndarray,
    layout: BlockLayout,
    *,
    weight: float,
) -> np.ndarray:
    if weight <= 0:
        raise ValueError("residual weight must be positive")
    lookup = np.empty((int(np.max(groups)) + 1,) * 2, dtype=np.int64)
    for (left, right), index in layout.pair_to_index.items():
        lookup[left, right] = index
        lookup[right, left] = index
    indices = lookup[groups[pairs[:, 0]], groups[pairs[:, 1]]]
    return np.asarray(public_scores, dtype=np.float64) + weight * residuals[indices]
