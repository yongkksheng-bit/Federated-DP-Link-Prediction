"""Inference-closed GAP-style aggregation adapted to link prediction.

This is an adaptation of GAP's perturb-message-normalize construction, not an
official reproduction of its node-classification architecture.
"""

from __future__ import annotations

import pathlib

import numpy as np
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from threadpoolctl import threadpool_limits


UNDIRECTED_EDGE_L2_SENSITIVITY = np.sqrt(2.0)


def normalize_rows(features: np.ndarray) -> np.ndarray:
    values = np.asarray(features, dtype=np.float64)
    if values.ndim != 2:
        raise ValueError("features must be a matrix")
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return np.divide(values, norms, out=np.zeros_like(values), where=norms > 0)


def public_svd_encoder(
    features: sparse.csr_matrix,
    *,
    dimension: int,
    random_state: int,
) -> np.ndarray:
    """Construct a graph-independent, row-bounded public encoder."""
    if dimension <= 0:
        raise ValueError("dimension must be positive")
    matrix = sparse.csr_matrix(features, dtype=np.float64)
    if matrix.shape[1] <= dimension:
        encoded = matrix.toarray()
    else:
        encoded = TruncatedSVD(
            n_components=dimension,
            algorithm="randomized",
            n_iter=7,
            random_state=random_state,
        ).fit_transform(matrix)
    return normalize_rows(encoded)


def cached_public_svd_encoder(
    features: sparse.csr_matrix,
    *,
    dimension: int,
    random_state: int,
    cache_path: pathlib.Path,
) -> np.ndarray:
    """Load or atomically cache a graph-independent public SVD encoding."""
    matrix = sparse.csr_matrix(features)
    cache_path = pathlib.Path(cache_path)
    if cache_path.exists():
        with np.load(cache_path, allow_pickle=False) as cached:
            encoded = cached["encoded"]
            shape = tuple(int(value) for value in cached["feature_shape"])
            cached_dimension = int(cached["requested_dimension"])
            cached_state = int(cached["random_state"])
            cached_nnz = int(cached["feature_nnz"])
        if (
            shape != matrix.shape
            or cached_dimension != dimension
            or cached_state != random_state
            or cached_nnz != matrix.nnz
        ):
            raise ValueError("public encoding cache metadata mismatch")
        return normalize_rows(encoded)
    # Sparse randomized SVD can become pathologically slow when multiple BLAS
    # runtimes oversubscribe the same cores. Limiting only this public
    # preprocessing block preserves the algorithm and deterministic seed.
    with threadpool_limits(limits=1):
        encoded = public_svd_encoder(
            matrix, dimension=dimension, random_state=random_state
        )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache_path.with_suffix(".tmp.npz")
    np.savez(
        temporary,
        encoded=encoded,
        feature_shape=np.asarray(matrix.shape, dtype=np.int64),
        feature_nnz=np.asarray(matrix.nnz, dtype=np.int64),
        requested_dimension=np.asarray(dimension, dtype=np.int64),
        random_state=np.asarray(random_state, dtype=np.int64),
    )
    temporary.replace(cache_path)
    return encoded


def client_owned_edges(
    edges: np.ndarray, homes: np.ndarray, *, clients: int
) -> tuple[np.ndarray, ...]:
    """Assign each canonical edge to the home of its first endpoint."""
    values = np.asarray(edges, dtype=np.int64)
    homes = np.asarray(homes, dtype=np.int64)
    if values.ndim != 2 or values.shape[1] != 2:
        raise ValueError("edges must have shape [m,2]")
    if clients <= 0 or np.any(homes < 0) or np.any(homes >= clients):
        raise ValueError("invalid client homes")
    owners = homes[values[:, 0]]
    return tuple(values[owners == client] for client in range(clients))


def undirected_sum_aggregation(
    edges: np.ndarray, features: np.ndarray
) -> np.ndarray:
    """Return A X for a canonical undirected edge list without self loops."""
    edges = np.asarray(edges, dtype=np.int64)
    features = np.asarray(features, dtype=np.float64)
    output = np.zeros_like(features)
    if len(edges):
        np.add.at(output, edges[:, 0], features[edges[:, 1]])
        np.add.at(output, edges[:, 1], features[edges[:, 0]])
    return output


def undirected_adjacency(
    local_edges: tuple[np.ndarray, ...], num_nodes: int
) -> sparse.csr_matrix:
    """Build the private CSR adjacency once for repeated validation queries."""
    edges = np.row_stack(local_edges) if local_edges else np.empty((0, 2), dtype=int)
    rows = np.concatenate([edges[:, 0], edges[:, 1]])
    columns = np.concatenate([edges[:, 1], edges[:, 0]])
    return sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.float64), (rows, columns)),
        shape=(num_nodes, num_nodes),
    )


def release_private_aggregations(
    local_edges: tuple[np.ndarray, ...],
    public_encoded: np.ndarray,
    *,
    hops: int,
    noise_std: float,
    visibility: str,
    rng: np.random.Generator,
    adjacency: sparse.csr_matrix | None = None,
) -> tuple[np.ndarray, ...]:
    """Release and cache normalized noisy aggregation channels.

    Each hop is one adaptive Gaussian query with undirected-edge L2
    sensitivity sqrt(2). Under ``visible_messages`` every client perturbs its
    own full matrix before the server sums messages. Under ``ideal_secagg`` a
    single perturbation is applied to the aggregate.
    """
    if not local_edges or hops <= 0 or noise_std <= 0:
        raise ValueError("local edges, positive hops, and positive noise are required")
    current = normalize_rows(public_encoded)
    if adjacency is not None and adjacency.shape != (len(current), len(current)):
        raise ValueError("adjacency shape must match encoded nodes")
    channels = [current]
    for _ in range(hops):
        aggregate = (
            adjacency @ current
            if adjacency is not None
            else sum(
                (undirected_sum_aggregation(edges, current) for edges in local_edges),
                start=np.zeros_like(current),
            )
        )
        if visibility == "visible_messages":
            # The server sum of K independent N(0, sigma^2 I) client noises is
            # exactly N(0, K sigma^2 I). Sampling that sum directly avoids K
            # redundant dense matrices without changing its distribution.
            aggregate += rng.normal(
                0.0, noise_std * np.sqrt(len(local_edges)), size=aggregate.shape
            )
        elif visibility == "ideal_secagg":
            aggregate += rng.normal(0.0, noise_std, size=aggregate.shape)
        else:
            raise ValueError("unknown visibility model")
        current = normalize_rows(aggregate)
        channels.append(current)
    return tuple(channels)


def score_pairs_from_channels(
    channels: tuple[np.ndarray, ...], pairs: np.ndarray
) -> np.ndarray:
    """Score candidate pairs by equal-weight cosine across cached channels."""
    if not channels:
        raise ValueError("at least one channel is required")
    pairs = np.asarray(pairs, dtype=np.int64)
    scores = np.zeros(len(pairs), dtype=np.float64)
    for channel in channels:
        normalized = normalize_rows(channel)
        scores += np.einsum(
            "ij,ij->i", normalized[pairs[:, 0]], normalized[pairs[:, 1]]
        )
    return scores / len(channels)
