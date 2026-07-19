"""Conservative centralized edge-DP pair classifier baseline."""

from __future__ import annotations

import numpy as np

from .pair_release import symmetric_pair_features


EDGE_RECORD_MULTIPLICITY = 3


def canonical_edge_keys(edges: np.ndarray, num_nodes: int) -> set[int]:
    values = np.asarray(edges, dtype=np.int64)
    if values.ndim != 2 or values.shape[1] != 2:
        raise ValueError("edges must have shape [m,2]")
    left = np.minimum(values[:, 0], values[:, 1])
    right = np.maximum(values[:, 0], values[:, 1])
    return set((left * num_nodes + right).tolist())


def stable_negative_pairs(
    num_nodes: int,
    positive_edges: np.ndarray,
    *,
    count: int,
    seed: int,
) -> np.ndarray:
    """Select negatives from a graph-independent proposal stream.

    Adding one edge can remove at most one accepted negative and admit the next
    proposal, giving one deletion and one insertion in addition to the new
    positive record.
    """
    if num_nodes < 2 or count <= 0:
        raise ValueError("num_nodes and count must be positive")
    positives = canonical_edge_keys(positive_edges, num_nodes)
    rng = np.random.default_rng(seed)
    seen: set[int] = set()
    accepted = []
    while len(accepted) < count:
        batch = max(4096, 2 * (count - len(accepted)))
        endpoints = rng.integers(0, num_nodes, size=(batch, 2), dtype=np.int64)
        for u, v in endpoints:
            if u == v:
                continue
            left, right = (int(u), int(v)) if u < v else (int(v), int(u))
            key = left * num_nodes + right
            if key in seen:
                continue
            seen.add(key)
            if key not in positives:
                accepted.append((left, right))
                if len(accepted) == count:
                    break
    return np.asarray(accepted, dtype=np.int64)


def bounded_pair_design(encoded: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    """Return public symmetric pair features with a bias and row norm <= 1."""
    pair = symmetric_pair_features(encoded, pairs)
    design = np.column_stack([np.ones(len(pair), dtype=np.float64), pair])
    norms = np.linalg.norm(design, axis=1, keepdims=True)
    return design / np.maximum(norms, 1.0)


def sigmoid(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    output = np.empty_like(values)
    positive = values >= 0
    output[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exp_values = np.exp(values[~positive])
    output[~positive] = exp_values / (1.0 + exp_values)
    return output


def clipped_gradient_sum(
    design: np.ndarray,
    labels: np.ndarray,
    weights: np.ndarray,
    *,
    clip_norm: float,
) -> np.ndarray:
    errors = sigmoid(design @ weights) - np.asarray(labels, dtype=np.float64)
    row_norms = np.linalg.norm(design, axis=1)
    norms = np.abs(errors) * row_norms
    if np.all(norms <= clip_norm):
        return design.T @ errors
    scales = np.minimum(1.0, clip_norm / np.maximum(norms, np.finfo(float).tiny))
    return design.T @ (errors * scales)


def train_private_logistic(
    design: np.ndarray,
    labels: np.ndarray,
    *,
    steps: int,
    learning_rate: float,
    clip_norm: float,
    noise_std: float,
    l2_penalty: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Train with full-batch clipped Gaussian gradients."""
    if steps <= 0 or learning_rate <= 0 or clip_norm <= 0 or noise_std <= 0:
        raise ValueError("optimizer and privacy parameters must be positive")
    weights = np.zeros(design.shape[1], dtype=np.float64)
    for _ in range(steps):
        gradient = clipped_gradient_sum(
            design, labels, weights, clip_norm=clip_norm
        )
        gradient += rng.normal(0.0, noise_std, size=gradient.shape)
        gradient /= len(labels)
        gradient += l2_penalty * weights
        weights -= learning_rate * gradient
    return weights
