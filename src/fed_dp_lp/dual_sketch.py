"""Joint semantic/topological DP sketches for link-prediction development."""

from __future__ import annotations

import numpy as np

from .gap_adaptation import normalize_rows


def public_rademacher_signatures(
    nodes: int, *, dimension: int, seed: int
) -> np.ndarray:
    if nodes <= 0 or dimension <= 0:
        raise ValueError("nodes and dimension must be positive")
    rng = np.random.default_rng(seed)
    signs = rng.integers(0, 2, size=(nodes, dimension), dtype=np.int8)
    return (2.0 * signs.astype(np.float64) - 1.0) / np.sqrt(dimension)


def joint_public_query(
    semantic: np.ndarray, topology: np.ndarray, *, semantic_fraction: float
) -> np.ndarray:
    if semantic.shape[0] != topology.shape[0] or not 0 <= semantic_fraction <= 1:
        raise ValueError("channels must share nodes and fraction must be in [0,1]")
    semantic = normalize_rows(semantic)
    topology = normalize_rows(topology)
    return np.column_stack(
        [
            np.sqrt(semantic_fraction) * semantic,
            np.sqrt(1.0 - semantic_fraction) * topology,
        ]
    )


def pair_cosine(channel: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    normalized = normalize_rows(channel)
    return np.einsum(
        "ij,ij->i", normalized[pairs[:, 0]], normalized[pairs[:, 1]]
    )


def topology_pair_score(
    channel: np.ndarray,
    pairs: np.ndarray,
    *,
    mode: str,
    effective_noise_std: float,
) -> np.ndarray:
    if mode == "topology_cosine":
        return pair_cosine(channel, pairs)
    if mode == "noise_standardized_dot":
        if effective_noise_std <= 0:
            raise ValueError("effective noise must be positive")
        raw = np.einsum(
            "ij,ij->i", channel[pairs[:, 0]], channel[pairs[:, 1]]
        )
        noise_scale = effective_noise_std**2 * np.sqrt(channel.shape[1])
        return np.tanh(raw / max(noise_scale, np.finfo(float).tiny))
    raise ValueError("unknown topology score mode")


def score_dual_sketch_pairs(
    public_scores: np.ndarray,
    released: np.ndarray,
    pairs: np.ndarray,
    *,
    semantic_dimension: int,
    mode: str,
    effective_noise_std: float,
    public_weight: float,
    semantic_weight: float,
    topology_weight: float,
) -> np.ndarray:
    if min(public_weight, semantic_weight, topology_weight) <= 0:
        raise ValueError("decoder weights must be positive")
    semantic = released[:, :semantic_dimension]
    topology = released[:, semantic_dimension:]
    if semantic.shape[1] == 0 or topology.shape[1] == 0:
        raise ValueError("both released channels must be nonempty")
    semantic_scores = pair_cosine(semantic, pairs)
    topology_scores = topology_pair_score(
        topology,
        pairs,
        mode=mode,
        effective_noise_std=effective_noise_std,
    )
    total = public_weight + semantic_weight + topology_weight
    return (
        public_weight * np.asarray(public_scores)
        + semantic_weight * semantic_scores
        + topology_weight * topology_scores
    ) / total
