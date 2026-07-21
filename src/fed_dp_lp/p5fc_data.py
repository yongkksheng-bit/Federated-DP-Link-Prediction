"""Strict loaders for the fresh GraphSAINT frontier sources."""

from __future__ import annotations

import pathlib

import numpy as np
from scipy import sparse


UINT64_MASK = np.uint64(0xFFFFFFFFFFFFFFFF)


def load_graphsaint_adjacency(path: pathlib.Path) -> sparse.csr_matrix:
    with np.load(path, allow_pickle=False) as source:
        required = {"data", "indices", "indptr", "shape"}
        if not required.issubset(source.files):
            raise ValueError(f"missing adjacency arrays: {required - set(source.files)}")
        shape = tuple(int(value) for value in source["shape"])
        adjacency = sparse.csr_matrix(
            (source["data"], source["indices"], source["indptr"]),
            shape=shape,
        )
    adjacency.sum_duplicates()
    adjacency.eliminate_zeros()
    return adjacency


def canonical_undirected_edges(adjacency: sparse.csr_matrix) -> np.ndarray:
    if adjacency.ndim != 2 or adjacency.shape[0] != adjacency.shape[1]:
        raise ValueError("adjacency must be square")
    graph = adjacency.maximum(adjacency.T).tocsr(copy=False)
    diagonal = graph.diagonal()
    if np.any(diagonal):
        graph = graph - sparse.diags(diagonal)
    graph.eliminate_zeros()
    upper = sparse.triu(graph, k=1, format="coo")
    edges = np.column_stack([upper.row, upper.col]).astype(np.int64, copy=False)
    return edges[np.lexsort((edges[:, 1], edges[:, 0]))]


def feature_matrix_audit(path: pathlib.Path, *, chunk_rows: int = 8192) -> dict:
    features = np.load(path, mmap_mode="r", allow_pickle=False)
    if features.ndim != 2 or not np.issubdtype(features.dtype, np.number):
        raise ValueError("features must be a numeric matrix")
    finite = True
    for start in range(0, features.shape[0], chunk_rows):
        finite = finite and bool(
            np.isfinite(features[start : start + chunk_rows]).all()
        )
        if not finite:
            break
    return {
        "shape": [int(value) for value in features.shape],
        "dtype": str(features.dtype),
        "all_finite": finite,
    }


def splitmix64(values: np.ndarray, *, seed: int) -> np.ndarray:
    """Return deterministic keyed 64-bit ranks without Python objects."""
    x = np.asarray(values, dtype=np.uint64) ^ np.uint64(seed)
    with np.errstate(over="ignore"):
        x = (x + np.uint64(0x9E3779B97F4A7C15)) & UINT64_MASK
        x = ((x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9))
        x &= UINT64_MASK
        x = ((x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB))
        x &= UINT64_MASK
    return x ^ (x >> np.uint64(31))


def edge_keys(edges: np.ndarray, *, nodes: int) -> np.ndarray:
    edges = np.asarray(edges)
    if edges.ndim != 2 or edges.shape[1] != 2 or nodes <= 1:
        raise ValueError("invalid canonical edge matrix or node count")
    return (
        edges[:, 0].astype(np.uint64) * np.uint64(nodes)
        + edges[:, 1].astype(np.uint64)
    )


def capped_stratified_positive_split(
    edges: np.ndarray,
    homes: np.ndarray,
    *,
    seed: int,
    validation_cap: int,
    test_cap: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Select capped validation/test positives by deterministic hash rank."""
    edges = np.asarray(edges, dtype=np.int64)
    homes = np.asarray(homes, dtype=np.int64)
    if validation_cap <= 0 or test_cap <= 0:
        raise ValueError("positive caps must be positive")
    nodes = len(homes)
    keys = edge_keys(edges, nodes=nodes)
    cross_mask = homes[edges[:, 0]] != homes[edges[:, 1]]
    heldout = np.zeros(len(edges), dtype=bool)
    validation_parts = []
    test_parts = []
    for cross in (False, True):
        indices = np.flatnonzero(cross_mask == cross)
        validation_count = validation_cap // 2 + (
            1 if not cross and validation_cap % 2 else 0
        )
        test_count = test_cap // 2 + (1 if not cross and test_cap % 2 else 0)
        total = validation_count + test_count
        if len(indices) < total:
            raise ValueError("a positive stratum is smaller than the frozen cap")
        ranks = splitmix64(keys[indices], seed=seed)
        selected_local = np.argpartition(ranks, total - 1)[:total]
        selected = indices[selected_local]
        order = np.lexsort((keys[selected], ranks[selected_local]))
        selected = selected[order]
        validation_parts.append(edges[selected[:validation_count]])
        test_parts.append(edges[selected[validation_count:]])
        heldout[selected] = True
    validation = np.concatenate(validation_parts).astype(np.int32, copy=False)
    test = np.concatenate(test_parts).astype(np.int32, copy=False)
    train = edges[~heldout].astype(np.int32, copy=False)
    return train, validation, test


def sample_stratified_nonedges(
    edges: np.ndarray,
    homes: np.ndarray,
    *,
    seed: int,
    validation_cap: int,
    test_cap: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Sample disjoint nonedges with frozen intra/cross counts."""
    edges = np.asarray(edges, dtype=np.int64)
    homes = np.asarray(homes, dtype=np.int64)
    nodes = len(homes)
    existing = np.sort(edge_keys(edges, nodes=nodes))
    rng = np.random.default_rng(seed)
    selected: set[int] = set()
    validation_parts = []
    test_parts = []
    for cross in (False, True):
        validation_count = validation_cap // 2 + (
            1 if not cross and validation_cap % 2 else 0
        )
        test_count = test_cap // 2 + (1 if not cross and test_cap % 2 else 0)
        required = validation_count + test_count
        accepted: list[tuple[int, int]] = []
        while len(accepted) < required:
            batch = max(4096, 4 * (required - len(accepted)))
            left = rng.integers(0, nodes, size=batch, dtype=np.int64)
            right = rng.integers(0, nodes, size=batch, dtype=np.int64)
            low, high = np.minimum(left, right), np.maximum(left, right)
            valid = (low != high) & ((homes[low] != homes[high]) == cross)
            low, high = low[valid], high[valid]
            candidate_keys = (
                low.astype(np.uint64) * np.uint64(nodes)
                + high.astype(np.uint64)
            )
            positions = np.searchsorted(existing, candidate_keys)
            is_edge = (positions < len(existing)) & (
                existing[np.minimum(positions, len(existing) - 1)] == candidate_keys
            )
            for u, v, key in zip(
                low[~is_edge], high[~is_edge], candidate_keys[~is_edge], strict=True
            ):
                integer_key = int(key)
                if integer_key in selected:
                    continue
                selected.add(integer_key)
                accepted.append((int(u), int(v)))
                if len(accepted) == required:
                    break
        values = np.asarray(accepted, dtype=np.int32)
        validation_parts.append(values[:validation_count])
        test_parts.append(values[validation_count:])
    return np.concatenate(validation_parts), np.concatenate(test_parts)
