"""Synthetic-only graph generator used by the preregistered P1 gate."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SyntheticGraph:
    groups: np.ndarray
    homes: np.ndarray
    client_edges: tuple[np.ndarray, ...]
    positive_pairs: np.ndarray
    negative_pairs: np.ndarray
    true_probabilities: np.ndarray


def _balanced_labels(size: int, classes: int, rng: np.random.Generator) -> np.ndarray:
    labels = np.arange(size, dtype=np.int64) % classes
    rng.shuffle(labels)
    return labels


def generate_sbm(
    *,
    nodes: int,
    groups_count: int,
    clients: int,
    within_probability: float,
    between_probability: float,
    train_retention: float,
    seed: int,
) -> SyntheticGraph:
    if not 0 < between_probability < within_probability < 1:
        raise ValueError("probabilities must satisfy 0 < between < within < 1")
    if not 0 < train_retention < 1:
        raise ValueError("train_retention must lie between zero and one")
    rng = np.random.default_rng(seed)
    groups = _balanced_labels(nodes, groups_count, rng)
    homes = _balanced_labels(nodes, clients, rng)
    pairs = np.asarray(
        [(u, v) for u in range(nodes) for v in range(u + 1, nodes)],
        dtype=np.int64,
    )
    same = groups[pairs[:, 0]] == groups[pairs[:, 1]]
    probabilities = np.where(same, within_probability, between_probability)
    exists = rng.random(len(pairs)) < probabilities
    retained = exists & (rng.random(len(pairs)) < train_retention)
    held_out = exists & ~retained
    train_edges = pairs[retained]

    # Public canonical ownership: the lower endpoint's fixed home client.
    owners = homes[train_edges[:, 0]] if len(train_edges) else np.empty(0, dtype=int)
    client_edges = tuple(train_edges[owners == k] for k in range(clients))
    positive_pairs = pairs[held_out]
    all_negatives = pairs[~exists]
    negative_count = min(len(positive_pairs), len(all_negatives))
    selected = rng.choice(len(all_negatives), size=negative_count, replace=False)
    negative_pairs = all_negatives[selected]
    candidate_pairs = np.concatenate([positive_pairs, negative_pairs], axis=0)
    candidate_true_probabilities = np.where(
        groups[candidate_pairs[:, 0]] == groups[candidate_pairs[:, 1]],
        within_probability,
        between_probability,
    )
    return SyntheticGraph(
        groups=groups,
        homes=homes,
        client_edges=client_edges,
        positive_pairs=positive_pairs,
        negative_pairs=negative_pairs,
        true_probabilities=candidate_true_probabilities,
    )
