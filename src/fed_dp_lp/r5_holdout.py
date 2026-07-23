"""Registered R5 holdout partitioning and finite-population utilities."""

from __future__ import annotations

import hashlib

import numpy as np


UINT64_SCALE = float(2**64)


def canonical_edge_keys(edges: np.ndarray, *, nodes: int) -> np.ndarray:
    """Encode canonical undirected edges as unique uint64 integers."""
    pairs = np.asarray(edges, dtype=np.int64)
    if pairs.ndim != 2 or pairs.shape[1] != 2 or nodes <= 1:
        raise ValueError("edges must have shape [m,2] and nodes must exceed one")
    low = np.minimum(pairs[:, 0], pairs[:, 1])
    high = np.maximum(pairs[:, 0], pairs[:, 1])
    if np.any(low < 0) or np.any(high >= nodes) or np.any(low == high):
        raise ValueError("invalid canonical edge")
    return low.astype(np.uint64) * np.uint64(nodes) + high.astype(np.uint64)


def _keyed_uniforms(
    edges: np.ndarray, *, nodes: int, dataset: str, seed: int, salt: str
) -> np.ndarray:
    keys = canonical_edge_keys(edges, nodes=nodes)
    output = np.empty(len(keys), dtype=np.float64)
    prefix = f"{salt}|{dataset}|{seed}|".encode("utf-8")
    for index, key in enumerate(keys):
        digest = hashlib.sha256(prefix + str(int(key)).encode("ascii")).digest()
        output[index] = int.from_bytes(digest[:8], "big") / UINT64_SCALE
    return output


def certification_mask(
    edges: np.ndarray,
    *,
    nodes: int,
    dataset: str,
    seed: int,
    salt: str,
    probability: float,
) -> np.ndarray:
    """Return a stable Bernoulli hash assignment to certification.

    Under the registered random-oracle interpretation, conditioning on the
    realized count yields a simple random sample without replacement from the
    sealed holdout population. Existing assignments do not change when an edge
    is added or removed.
    """
    if not 0.0 < probability < 1.0:
        raise ValueError("probability must lie strictly between zero and one")
    return _keyed_uniforms(
        edges, nodes=nodes, dataset=dataset, seed=seed, salt=salt
    ) < probability


def corrupted_pairs(
    edges: np.ndarray,
    *,
    nodes: int,
    dataset: str,
    seed: int,
    salt: str,
) -> np.ndarray:
    """Create one graph-independent endpoint corruption per positive edge."""
    pairs = np.asarray(edges, dtype=np.int64)
    uniforms = _keyed_uniforms(
        pairs, nodes=nodes, dataset=dataset, seed=seed, salt=salt
    )
    replacements = np.floor(uniforms * nodes).astype(np.int64)
    output = np.empty_like(pairs)
    output[:, 0] = pairs[:, 0]
    for index, (left, right) in enumerate(pairs):
        replacement = int(replacements[index])
        while replacement == left or replacement == right:
            replacement = (replacement + 1) % nodes
        output[index, 1] = replacement
    output.sort(axis=1)
    return output


def ranking_advantage(
    candidate_positive: np.ndarray,
    candidate_corrupted: np.ndarray,
    public_positive: np.ndarray,
    public_corrupted: np.ndarray,
) -> np.ndarray:
    """Return candidate-minus-public pairwise ranking utility in [-1,1]."""
    arrays = [
        np.asarray(values, dtype=np.float64)
        for values in (
            candidate_positive,
            candidate_corrupted,
            public_positive,
            public_corrupted,
        )
    ]
    if len({values.shape for values in arrays}) != 1:
        raise ValueError("score arrays must have identical shapes")

    def utility(positive: np.ndarray, corrupted: np.ndarray) -> np.ndarray:
        return (positive > corrupted).astype(np.float64) + 0.5 * (
            positive == corrupted
        )

    return utility(arrays[0], arrays[1]) - utility(arrays[2], arrays[3])


def finite_population_penalty(
    certification_count: int,
    population_count: int,
    *,
    failure_probability: float,
) -> float:
    """One-sided Serfling penalty for values in [-1,1].

    The finite-population correction is valid conditional on the Bernoulli
    hash sample size. Returning infinity for degenerate samples forces
    abstention.
    """
    n = int(certification_count)
    population = int(population_count)
    if not 0.0 < failure_probability < 1.0:
        raise ValueError("failure_probability must lie in (0,1)")
    if n <= 0 or population <= n:
        return float("inf")
    correction = 1.0 - (n - 1.0) / population
    return float(
        np.sqrt(2.0 * correction * np.log(1.0 / failure_probability) / n)
    )
