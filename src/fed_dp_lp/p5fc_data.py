"""Strict loaders for the fresh GraphSAINT frontier sources."""

from __future__ import annotations

import pathlib

import numpy as np
from scipy import sparse


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
    graph.setdiag(0)
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
