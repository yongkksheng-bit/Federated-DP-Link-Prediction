"""Sensitivity-one soft pair-feature sufficient-statistic release."""

from __future__ import annotations

from itertools import combinations

import numpy as np


def normalize_rows(features: np.ndarray) -> np.ndarray:
    features = np.asarray(features, dtype=np.float64)
    norms = np.linalg.norm(features, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("public feature rows must be nonzero")
    return features / norms


def symmetric_pair_features(features: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    """Return an isometric vectorization of symmetrized outer products."""
    features = np.asarray(features, dtype=np.float64)
    pairs = np.asarray(pairs, dtype=np.int64)
    left = features[pairs[:, 0]]
    right = features[pairs[:, 1]]
    dimension = features.shape[1]
    columns = [left[:, idx] * right[:, idx] for idx in range(dimension)]
    scale = 1.0 / np.sqrt(2.0)
    columns.extend(
        scale * (left[:, i] * right[:, j] + left[:, j] * right[:, i])
        for i, j in combinations(range(dimension), 2)
    )
    return np.column_stack(columns)


def release_pair_statistic(
    client_edges: tuple[np.ndarray, ...],
    features: np.ndarray,
    *,
    noise_std: float,
    visibility: str,
    rng: np.random.Generator,
) -> np.ndarray:
    if noise_std <= 0 or not client_edges:
        raise ValueError("positive noise_std and at least one client are required")
    local = []
    output_dimension = features.shape[1] * (features.shape[1] + 1) // 2
    for edges in client_edges:
        if len(edges):
            local.append(np.sum(symmetric_pair_features(features, edges), axis=0))
        else:
            local.append(np.zeros(output_dimension, dtype=np.float64))
    local = np.stack(local)
    if visibility == "ideal_secagg":
        return np.sum(local, axis=0) + rng.normal(0.0, noise_std, output_dimension)
    if visibility == "visible_messages":
        return np.sum(
            local + rng.normal(0.0, noise_std, size=local.shape), axis=0
        )
    raise ValueError("unknown visibility model")


def fit_public_ridge(
    all_pair_features: np.ndarray, released_statistic: np.ndarray
) -> np.ndarray:
    gram = all_pair_features.T @ all_pair_features
    ridge = 1e-3 * float(np.trace(gram)) / gram.shape[0]
    return np.linalg.solve(gram + ridge * np.eye(gram.shape[0]), released_statistic)
