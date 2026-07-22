"""Training-only graph-domain properties for feasibility-boundary analysis."""

from __future__ import annotations

import math

import networkx as nx
import numpy as np
from scipy import sparse


def degree_gini(degrees: np.ndarray) -> float:
    """Return the Gini coefficient of a nonnegative degree vector."""
    values = np.asarray(degrees, dtype=np.float64)
    if values.ndim != 1 or np.any(values < 0):
        raise ValueError("degrees must be a one-dimensional nonnegative vector")
    total = float(values.sum())
    if values.size == 0 or total == 0.0:
        return 0.0
    ordered = np.sort(values)
    ranks = np.arange(1, len(ordered) + 1, dtype=np.float64)
    return float((2.0 * np.dot(ranks, ordered) / total - len(ordered) - 1) / len(ordered))


def training_adjacency(node_count: int, edges: np.ndarray) -> sparse.csr_matrix:
    """Build a canonical undirected binary adjacency matrix."""
    pairs = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    if len(pairs) and (
        pairs.min() < 0 or pairs.max() >= node_count or np.any(pairs[:, 0] >= pairs[:, 1])
    ):
        raise ValueError("edges must be canonical, loop-free, and in range")
    rows = np.concatenate((pairs[:, 0], pairs[:, 1]))
    columns = np.concatenate((pairs[:, 1], pairs[:, 0]))
    return sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.float64), (rows, columns)),
        shape=(node_count, node_count),
    )


def common_neighbor_scores(adjacency: sparse.csr_matrix, pairs: np.ndarray) -> np.ndarray:
    """Vectorized common-neighbor counts for candidate pairs."""
    candidates = np.asarray(pairs, dtype=np.int64).reshape(-1, 2)
    products = adjacency[candidates[:, 0]].multiply(adjacency[candidates[:, 1]])
    return np.asarray(products.sum(axis=1)).ravel().astype(np.float64)


def sampled_average_clustering(
    graph: nx.Graph, *, node_cap: int, seed: int
) -> float:
    """Average exact local clustering on a deterministic node sample."""
    nodes = np.asarray(sorted(graph.nodes()), dtype=np.int64)
    if len(nodes) == 0:
        return 0.0
    if len(nodes) > node_cap:
        rng = np.random.default_rng(seed)
        nodes = np.sort(rng.choice(nodes, size=node_cap, replace=False))
    values = nx.clustering(graph, nodes.tolist())
    return float(np.mean([values[int(node)] for node in nodes]))


def topology_properties(
    node_count: int,
    train_positive: np.ndarray,
    homes: np.ndarray,
    *,
    clustering_node_cap: int,
    clustering_seed: int,
    louvain_resolution: float,
    louvain_seed: int,
) -> tuple[dict[str, float | int], sparse.csr_matrix]:
    """Compute topology and federated-layout properties from training edges."""
    adjacency = training_adjacency(node_count, train_positive)
    graph = nx.from_scipy_sparse_array(adjacency)
    degrees = np.asarray(adjacency.sum(axis=1)).ravel()
    mean_degree = float(degrees.mean())
    components = list(nx.connected_components(graph))
    largest_component_fraction = (
        float(max(map(len, components)) / node_count) if node_count else 0.0
    )
    assortativity = float(nx.degree_assortativity_coefficient(graph))
    if not math.isfinite(assortativity):
        assortativity = 0.0
    communities = nx.community.louvain_communities(
        graph,
        resolution=louvain_resolution,
        seed=louvain_seed,
    )
    modularity = float(
        nx.community.modularity(graph, communities, resolution=louvain_resolution)
    )
    pairs = np.asarray(train_positive, dtype=np.int64).reshape(-1, 2)
    cross_fraction = float(
        np.mean(homes[pairs[:, 0]] != homes[pairs[:, 1]])
    ) if len(pairs) else 0.0
    density = 2.0 * len(pairs) / max(node_count * (node_count - 1), 1)
    return {
        "edge_density": float(density),
        "mean_degree": mean_degree,
        "degree_cv": float(degrees.std() / max(mean_degree, np.finfo(float).tiny)),
        "degree_gini": degree_gini(degrees),
        "largest_component_fraction": largest_component_fraction,
        "sampled_average_clustering": sampled_average_clustering(
            graph, node_cap=clustering_node_cap, seed=clustering_seed
        ),
        "degree_assortativity": assortativity,
        "louvain_modularity": modularity,
        "louvain_communities": len(communities),
        "cross_client_edge_fraction": cross_fraction,
    }, adjacency


def public_descriptor_properties(features: sparse.csr_matrix) -> dict[str, float]:
    """Return descriptor coverage and matrix density without densification."""
    matrix = features.tocsr()
    coverage = float(np.mean(np.diff(matrix.indptr) > 0)) if matrix.shape[0] else 0.0
    denominator = matrix.shape[0] * matrix.shape[1]
    return {
        "public_feature_coverage": coverage,
        "public_feature_density": float(matrix.nnz / max(denominator, 1)),
    }
