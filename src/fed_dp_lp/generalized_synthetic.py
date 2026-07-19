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
