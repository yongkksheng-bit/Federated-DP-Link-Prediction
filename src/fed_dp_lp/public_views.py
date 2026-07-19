"""Deterministic public-view perturbations for synthetic stress tests."""

from __future__ import annotations

import numpy as np


def balanced_labels(size: int, classes: int, rng: np.random.Generator) -> np.ndarray:
    if size < 2 * classes:
        raise ValueError("each class must contain at least two nodes")
    labels = np.arange(size, dtype=np.int64) % classes
    rng.shuffle(labels)
    return labels


def corrupt_groups(
    groups: np.ndarray, fraction: float, rng: np.random.Generator
) -> np.ndarray:
    groups = np.asarray(groups, dtype=np.int64)
    classes = int(np.max(groups)) + 1
    if classes < 2 or not 0 <= fraction <= 1:
        raise ValueError("corruption requires at least two groups and fraction in [0,1]")
    result = groups.copy()
    count = int(round(fraction * len(groups)))
    if count == 0:
        return result
    indices = rng.choice(len(groups), size=count, replace=False)
    offsets = rng.integers(1, classes, size=count)
    result[indices] = (result[indices] + offsets) % classes
    return result


def refine_groups(
    groups: np.ndarray, factor: int, rng: np.random.Generator
) -> np.ndarray:
    groups = np.asarray(groups, dtype=np.int64)
    if factor < 1:
        raise ValueError("refinement factor must be positive")
    if factor == 1:
        return groups.copy()
    result = np.empty_like(groups)
    for group in np.unique(groups):
        indices = np.flatnonzero(groups == group)
        if len(indices) < 2 * factor:
            raise ValueError("every refined public group needs at least two nodes")
        shuffled = indices.copy()
        rng.shuffle(shuffled)
        subgroups = np.arange(len(indices), dtype=np.int64) % factor
        result[shuffled] = int(group) * factor + subgroups
    return result


def repartition_edges(
    edges: np.ndarray, homes: np.ndarray, clients: int
) -> tuple[np.ndarray, ...]:
    edges = np.asarray(edges, dtype=np.int64)
    homes = np.asarray(homes, dtype=np.int64)
    if np.any(homes < 0) or np.any(homes >= clients):
        raise ValueError("home labels must lie in the client range")
    owners = homes[edges[:, 0]] if len(edges) else np.empty(0, dtype=np.int64)
    return tuple(edges[owners == client] for client in range(clients))
