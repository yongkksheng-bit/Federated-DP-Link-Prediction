import numpy as np
from scipy import sparse

from fed_dp_lp.p5fc_data import (
    canonical_undirected_edges,
    feature_matrix_audit,
    load_graphsaint_adjacency,
)


def test_graphsaint_loader_and_canonicalization(tmp_path):
    adjacency = sparse.csr_matrix(
        np.asarray([[0, 1, 0], [1, 0, 2], [0, 0, 0]], dtype=np.float32)
    )
    path = tmp_path / "adj_full.npz"
    np.savez(
        path,
        data=adjacency.data,
        indices=adjacency.indices,
        indptr=adjacency.indptr,
        shape=np.asarray(adjacency.shape),
    )
    loaded = load_graphsaint_adjacency(path)
    edges = canonical_undirected_edges(loaded)
    assert edges.tolist() == [[0, 1], [1, 2]]


def test_feature_matrix_audit_uses_shape_dtype_and_finiteness(tmp_path):
    path = tmp_path / "feats.npy"
    np.save(path, np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32))
    audit = feature_matrix_audit(path, chunk_rows=1)
    assert audit == {
        "shape": [2, 2],
        "dtype": "float32",
        "all_finite": True,
    }
