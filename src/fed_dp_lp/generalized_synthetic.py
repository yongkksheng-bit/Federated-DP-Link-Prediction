"""Generalized SBM with arbitrary affinities and noisy public features."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .pair_release import normalize_rows
from .public_views import balanced_labels, repartition_edges


@dataclass(frozen=True)
class GeneralizedSyntheticGraph:
    latent_groups: np.ndarray
    public_features: np.ndarray
    homes: np.ndarray
    client_edges: tuple[np.ndarray, ...]
    positive_pairs: np.ndarray
    negative_pairs: np.ndarray
    true_probabilities: np.ndarray


@dataclass(frozen=True)
class ReciprocalPreferenceGraph:
    public_cells: np.ndarray
    latent_preferences: np.ndarray
    public_features: np.ndarray
    homes: np.ndarray
    client_edges: tuple[np.ndarray, ...]
    positive_pairs: np.ndarray
    negative_pairs: np.ndarray
    true_probabilities: np.ndarray


def generate_reciprocal_preference_graph(
    *,
    nodes: int,
    cells_count: int,
    clients: int,
    base_probability: float,
    one_sided_boost: float,
    mutual_boost: float,
    train_retention: float,
    feature_corruption: float,
    seed: int,
) -> ReciprocalPreferenceGraph:
    """Generate links from node-specific preferences for public endpoint cells."""
    if nodes < cells_count or cells_count < 2 or clients < 1:
        raise ValueError("invalid graph dimensions")
    if not 0 < train_retention < 1 or feature_corruption < 0:
        raise ValueError("invalid retention or feature corruption")
    if base_probability <= 0 or one_sided_boost <= 0 or mutual_boost < 0:
        raise ValueError("probability components must be positive")
    if base_probability + 2 * one_sided_boost + mutual_boost >= 1:
        raise ValueError("maximum edge probability must be below one")
    root = np.random.SeedSequence(seed)
    rng_cells, rng_preferences, rng_homes, rng_edges, rng_features = [
        np.random.default_rng(child) for child in root.spawn(5)
    ]
    cells = balanced_labels(nodes, cells_count, rng_cells)
    preferences = rng_preferences.integers(0, cells_count, size=nodes)
    homes = balanced_labels(nodes, clients, rng_homes)
    features = np.eye(cells_count)[cells] + feature_corruption * rng_features.normal(
        0.0, 1.0 / np.sqrt(cells_count), size=(nodes, cells_count)
    )
    features = normalize_rows(features)
    pairs = np.asarray(
        [(u, v) for u in range(nodes) for v in range(u + 1, nodes)],
        dtype=np.int64,
    )
    left_match = preferences[pairs[:, 0]] == cells[pairs[:, 1]]
    right_match = preferences[pairs[:, 1]] == cells[pairs[:, 0]]
    probabilities = (
        base_probability
        + one_sided_boost * (left_match.astype(float) + right_match.astype(float))
        + mutual_boost * (left_match & right_match)
    )
    exists = rng_edges.random(len(pairs)) < probabilities
    retained = exists & (rng_edges.random(len(pairs)) < train_retention)
    held_out = exists & ~retained
    train_edges = pairs[retained]
    client_edges = repartition_edges(train_edges, homes, clients)
    positives = pairs[held_out]
    negatives_all = pairs[~exists]
    count = min(len(positives), len(negatives_all))
    negatives = negatives_all[
        rng_edges.choice(len(negatives_all), size=count, replace=False)
    ]
    candidates = np.concatenate([positives, negatives], axis=0)
    candidate_left = preferences[candidates[:, 0]] == cells[candidates[:, 1]]
    candidate_right = preferences[candidates[:, 1]] == cells[candidates[:, 0]]
    candidate_probabilities = (
        base_probability
        + one_sided_boost
        * (candidate_left.astype(float) + candidate_right.astype(float))
        + mutual_boost * (candidate_left & candidate_right)
    )
    return ReciprocalPreferenceGraph(
        public_cells=cells,
        latent_preferences=preferences,
        public_features=features,
        homes=homes,
        client_edges=client_edges,
        positive_pairs=positives,
        negative_pairs=negatives,
        true_probabilities=candidate_probabilities,
    )


def generate_generalized_sbm(
    *,
    nodes: int,
    affinity: np.ndarray,
    clients: int,
    train_retention: float,
    feature_corruption: float,
    seed: int,
) -> GeneralizedSyntheticGraph:
    affinity = np.asarray(affinity, dtype=np.float64)
    groups_count = affinity.shape[0]
    if affinity.shape != (groups_count, groups_count) or not np.allclose(affinity, affinity.T):
        raise ValueError("affinity must be square and symmetric")
    if np.any(affinity <= 0) or np.any(affinity >= 1):
        raise ValueError("affinities must lie strictly between zero and one")
    rng_groups = np.random.default_rng(np.random.SeedSequence([seed, 11]))
    rng_homes = np.random.default_rng(np.random.SeedSequence([seed, 12]))
    rng_edges = np.random.default_rng(np.random.SeedSequence([seed, 13]))
    rng_features = np.random.default_rng(
        np.random.SeedSequence([seed, 14, int(feature_corruption * 1000)])
    )
    latent = balanced_labels(nodes, groups_count, rng_groups)
    homes = balanced_labels(nodes, clients, rng_homes)
    features = np.eye(groups_count)[latent] + feature_corruption * rng_features.normal(
        0.0, 1.0 / np.sqrt(groups_count), size=(nodes, groups_count)
    )
    features = normalize_rows(features)
    pairs = np.asarray(
        [(u, v) for u in range(nodes) for v in range(u + 1, nodes)], dtype=np.int64
    )
    probabilities = affinity[latent[pairs[:, 0]], latent[pairs[:, 1]]]
    exists = rng_edges.random(len(pairs)) < probabilities
    retained = exists & (rng_edges.random(len(pairs)) < train_retention)
    held_out = exists & ~retained
    train_edges = pairs[retained]
    client_edges = repartition_edges(train_edges, homes, clients)
    positives = pairs[held_out]
    all_negatives = pairs[~exists]
    count = min(len(positives), len(all_negatives))
    negatives = all_negatives[rng_edges.choice(len(all_negatives), size=count, replace=False)]
    candidates = np.concatenate([positives, negatives], axis=0)
    return GeneralizedSyntheticGraph(
        latent_groups=latent,
        public_features=features,
        homes=homes,
        client_edges=client_edges,
        positive_pairs=positives,
        negative_pairs=negatives,
        true_probabilities=affinity[
            latent[candidates[:, 0]], latent[candidates[:, 1]]
        ],
    )
