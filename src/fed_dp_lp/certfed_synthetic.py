"""End-to-end synthetic graph utilities for CertFed-LP."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .gap_adaptation import (
    client_owned_edges,
    normalize_rows,
    score_pairs_from_channels,
    undirected_sum_aggregation,
)
from .p5fc_data import edge_keys, splitmix64


@dataclass(frozen=True)
class SyntheticGraph:
    features: np.ndarray
    edges: np.ndarray
    homes: np.ndarray


@dataclass(frozen=True)
class TrainingRelease:
    channels: tuple[np.ndarray, ...]
    message_count: int
    aggregate_error: float


@dataclass(frozen=True)
class CertificationRelease:
    noisy_sum: float
    noisy_count: float
    message_count: int
    aggregate_error: float


def generate_sbm_graph(
    *,
    nodes: int,
    communities: int,
    clients: int,
    p_in: float,
    p_out: float,
    feature_noise: float,
    seed: int,
) -> SyntheticGraph:
    if nodes <= 1 or communities <= 1 or clients <= 0:
        raise ValueError("invalid synthetic graph dimensions")
    rng = np.random.default_rng(seed)
    labels = np.arange(nodes, dtype=np.int64) % communities
    rng.shuffle(labels)
    left, right = np.triu_indices(nodes, k=1)
    probabilities = np.where(labels[left] == labels[right], p_in, p_out)
    keep = rng.random(len(left)) < probabilities
    edges = np.column_stack((left[keep], right[keep])).astype(np.int64)
    features = np.eye(communities, dtype=np.float64)[labels]
    features += rng.normal(0.0, feature_noise, size=features.shape)
    homes = np.arange(nodes, dtype=np.int64) % clients
    return SyntheticGraph(
        features=normalize_rows(features),
        edges=edges,
        homes=homes,
    )


def partition_edges(
    edges: np.ndarray,
    *,
    nodes: int,
    seed: int,
    training_fraction: float,
    certification_fraction: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if training_fraction <= 0 or certification_fraction <= 0:
        raise ValueError("partition fractions must be positive")
    if training_fraction + certification_fraction >= 1:
        raise ValueError("partition fractions leave no evaluation split")
    keys = edge_keys(edges, nodes=nodes)
    ranks = splitmix64(keys, seed=seed)
    uniforms = ranks.astype(np.float64) / np.float64(2**64)
    training = uniforms < training_fraction
    certification = (
        (uniforms >= training_fraction)
        & (uniforms < training_fraction + certification_fraction)
    )
    return edges[training], edges[certification], edges[~(training | certification)]


def corrupted_pairs(edges: np.ndarray, *, nodes: int, seed: int) -> np.ndarray:
    keys = edge_keys(edges, nodes=nodes)
    ranks = splitmix64(keys, seed=seed)
    replacements = (ranks % np.uint64(nodes)).astype(np.int64)
    output = np.empty_like(edges)
    output[:, 0] = edges[:, 0]
    for index, (left, right) in enumerate(edges):
        replacement = int(replacements[index])
        while replacement == left or replacement == right:
            replacement = (replacement + 1) % nodes
        output[index, 1] = replacement
    output.sort(axis=1)
    return output


def release_training_channels(
    train_edges: np.ndarray,
    features: np.ndarray,
    homes: np.ndarray,
    *,
    clients: int,
    noise_std: float,
    visibility: str,
    rng: np.random.Generator,
) -> TrainingRelease:
    local_edges = client_owned_edges(train_edges, homes, clients=clients)
    current = normalize_rows(features)
    if visibility == "visible_messages":
        messages = tuple(
            undirected_sum_aggregation(edges, current)
            + rng.normal(0.0, noise_std, size=current.shape)
            for edges in local_edges
        )
        aggregate = sum(messages, start=np.zeros_like(current))
        direct = sum(
            (undirected_sum_aggregation(edges, current) for edges in local_edges),
            start=np.zeros_like(current),
        ) + sum(
            (message - undirected_sum_aggregation(edges, current)
             for message, edges in zip(messages, local_edges)),
            start=np.zeros_like(current),
        )
        error = float(np.max(np.abs(aggregate - direct)))
        message_count = clients
    elif visibility == "ideal_secagg":
        aggregate = sum(
            (undirected_sum_aggregation(edges, current) for edges in local_edges),
            start=np.zeros_like(current),
        )
        aggregate += rng.normal(0.0, noise_std, size=current.shape)
        error = 0.0
        message_count = 1
    else:
        raise ValueError("unknown visibility")
    return TrainingRelease(
        channels=(current, normalize_rows(aggregate)),
        message_count=message_count,
        aggregate_error=error,
    )


def pairwise_advantages(
    public_channels: tuple[np.ndarray, ...],
    structural_channels: tuple[np.ndarray, ...],
    edges: np.ndarray,
    comparisons: np.ndarray,
) -> np.ndarray:
    public_positive = score_pairs_from_channels(public_channels, edges)
    public_negative = score_pairs_from_channels(public_channels, comparisons)
    structural_positive = score_pairs_from_channels(structural_channels, edges)
    structural_negative = score_pairs_from_channels(
        structural_channels, comparisons
    )
    public_utility = (public_positive > public_negative).astype(float)
    public_utility += 0.5 * (public_positive == public_negative)
    structural_utility = (structural_positive > structural_negative).astype(float)
    structural_utility += 0.5 * (structural_positive == structural_negative)
    return structural_utility - public_utility


def release_certification_query(
    advantages: np.ndarray,
    owners: np.ndarray,
    *,
    clients: int,
    noise_std: float,
    visibility: str,
    rng: np.random.Generator,
) -> CertificationRelease:
    values = np.asarray(advantages, dtype=np.float64)
    owners = np.asarray(owners, dtype=np.int64)
    local = tuple(
        np.asarray([values[owners == client].sum(), np.sum(owners == client)])
        for client in range(clients)
    )
    if visibility == "visible_messages":
        messages = tuple(
            query + rng.normal(0.0, noise_std, size=2) for query in local
        )
        aggregate = sum(messages, start=np.zeros(2))
        direct = sum(local, start=np.zeros(2)) + sum(
            (message - query for message, query in zip(messages, local)),
            start=np.zeros(2),
        )
        error = float(np.max(np.abs(aggregate - direct)))
        message_count = clients
    elif visibility == "ideal_secagg":
        aggregate = sum(local, start=np.zeros(2))
        aggregate += rng.normal(0.0, noise_std, size=2)
        error = 0.0
        message_count = 1
    else:
        raise ValueError("unknown visibility")
    return CertificationRelease(
        noisy_sum=float(aggregate[0]),
        noisy_count=float(aggregate[1]),
        message_count=message_count,
        aggregate_error=error,
    )
