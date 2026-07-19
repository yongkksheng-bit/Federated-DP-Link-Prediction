"""Budget-coupled semantic aggregation and conditioned histogram release."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from .gap_adaptation import normalize_rows, score_pairs_from_channels
from .conditioned_release import ConditionedLayout, score_conditioned_pairs


JOINT_L2_SENSITIVITY = np.sqrt(2.0)


def joint_scales(histogram_energy_fraction: float) -> tuple[float, float]:
    gamma = float(histogram_energy_fraction)
    if not 0 < gamma < 1:
        raise ValueError("histogram energy fraction must lie in (0,1)")
    return np.sqrt(1.0 - gamma), np.sqrt(2.0 * gamma)


def release_joint_first_hop(
    adjacency: sparse.csr_matrix,
    encoded: np.ndarray,
    local_counts: tuple[np.ndarray, ...],
    *,
    histogram_energy_fraction: float,
    noise_std: float,
    visibility: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Return recovered noisy aggregation and histogram blocks."""
    if not local_counts or noise_std <= 0:
        raise ValueError("local counts and positive noise are required")
    encoded = normalize_rows(encoded)
    if adjacency.shape != (len(encoded), len(encoded)):
        raise ValueError("adjacency and encoded node count must match")
    dimensions = {np.asarray(value).shape for value in local_counts}
    if len(dimensions) != 1:
        raise ValueError("all local histograms must share shape")
    aggregation_scale, histogram_scale = joint_scales(histogram_energy_fraction)
    aggregation_signal = aggregation_scale * (adjacency @ encoded)
    histogram_signal = histogram_scale * np.sum(np.stack(local_counts), axis=0)
    if visibility == "visible_messages":
        effective_noise = noise_std * np.sqrt(len(local_counts))
    elif visibility == "ideal_secagg":
        effective_noise = noise_std
    else:
        raise ValueError("unknown visibility model")
    noisy_aggregation = aggregation_signal + rng.normal(
        0.0, effective_noise, size=aggregation_signal.shape
    )
    noisy_histogram = histogram_signal + rng.normal(
        0.0, effective_noise, size=histogram_signal.shape
    )
    return noisy_aggregation / aggregation_scale, noisy_histogram / histogram_scale


def score_joint_release_pairs(
    semantic_channels: tuple[np.ndarray, ...],
    public_scores: np.ndarray,
    pairs: np.ndarray,
    cells: np.ndarray,
    histogram_residual: np.ndarray,
    layout: ConditionedLayout,
    *,
    residual_weight: float,
) -> np.ndarray:
    gap_score = score_pairs_from_channels(semantic_channels, pairs)
    conditioned = score_conditioned_pairs(
        public_scores,
        pairs,
        cells,
        histogram_residual,
        layout,
        weight=residual_weight,
    )
    return gap_score + conditioned - public_scores
