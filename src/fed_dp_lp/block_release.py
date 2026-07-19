"""Inference-closed block-count release with edge sensitivity one."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations_with_replacement

import numpy as np


@dataclass(frozen=True)
class BlockLayout:
    pairs: tuple[tuple[int, int], ...]
    capacities: np.ndarray
    pair_to_index: dict[tuple[int, int], int]

    @property
    def dimension(self) -> int:
        return len(self.pairs)


def make_block_layout(groups: np.ndarray) -> BlockLayout:
    groups = np.asarray(groups, dtype=np.int64)
    if groups.ndim != 1 or groups.size < 2 or np.any(groups < 0):
        raise ValueError("groups must be a one-dimensional nonnegative vector")
    labels = tuple(int(x) for x in np.unique(groups))
    if labels != tuple(range(len(labels))):
        raise ValueError("group labels must be contiguous from zero")
    sizes = np.bincount(groups, minlength=len(labels))
    pairs = tuple(combinations_with_replacement(labels, 2))
    capacities = []
    for left, right in pairs:
        if left == right:
            capacities.append(sizes[left] * (sizes[left] - 1) // 2)
        else:
            capacities.append(sizes[left] * sizes[right])
    capacities_array = np.asarray(capacities, dtype=np.float64)
    if np.any(capacities_array <= 0):
        raise ValueError("every public group must contain at least two nodes")
    return BlockLayout(
        pairs=pairs,
        capacities=capacities_array,
        pair_to_index={pair: idx for idx, pair in enumerate(pairs)},
    )


def block_counts(
    edges: np.ndarray, groups: np.ndarray, layout: BlockLayout
) -> np.ndarray:
    edges = np.asarray(edges, dtype=np.int64)
    groups = np.asarray(groups, dtype=np.int64)
    if edges.size == 0:
        return np.zeros(layout.dimension, dtype=np.float64)
    if edges.ndim != 2 or edges.shape[1] != 2:
        raise ValueError("edges must have shape [num_edges, 2]")
    if np.any(edges < 0) or np.any(edges >= groups.size):
        raise ValueError("edge endpoint outside the public node universe")
    if np.any(edges[:, 0] >= edges[:, 1]):
        raise ValueError("edges must be canonical with u < v")
    counts = np.zeros(layout.dimension, dtype=np.float64)
    for u, v in edges:
        pair = tuple(sorted((int(groups[u]), int(groups[v]))))
        counts[layout.pair_to_index[pair]] += 1.0
    return counts


def release_block_densities(
    client_edges: tuple[np.ndarray, ...],
    groups: np.ndarray,
    *,
    noise_std: float,
    visibility: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, BlockLayout]:
    """Release noisy block counts and densities without retaining private edges."""
    if noise_std <= 0:
        raise ValueError("noise_std must be positive")
    if not client_edges:
        raise ValueError("at least one client is required")
    layout = make_block_layout(groups)
    local = np.stack([block_counts(e, groups, layout) for e in client_edges])
    if visibility == "visible_messages":
        noisy_counts = np.sum(
            local + rng.normal(0.0, noise_std, size=local.shape), axis=0
        )
    elif visibility == "ideal_secagg":
        noisy_counts = np.sum(local, axis=0) + rng.normal(
            0.0, noise_std, size=layout.dimension
        )
    else:
        raise ValueError("visibility must be visible_messages or ideal_secagg")
    densities = np.clip(noisy_counts / layout.capacities, 0.0, 1.0)
    return noisy_counts, densities, layout


def score_pairs(
    pairs: np.ndarray,
    groups: np.ndarray,
    densities: np.ndarray,
    layout: BlockLayout,
) -> np.ndarray:
    """Score public candidate pairs using only a DP release and public groups."""
    pairs = np.asarray(pairs, dtype=np.int64)
    block_count = int(np.max(groups)) + 1
    lookup = np.empty((block_count, block_count), dtype=np.int64)
    for block, idx in layout.pair_to_index.items():
        left, right = block
        lookup[left, right] = idx
        lookup[right, left] = idx
    left = groups[pairs[:, 0]]
    right = groups[pairs[:, 1]]
    return densities[lookup[left, right]]
