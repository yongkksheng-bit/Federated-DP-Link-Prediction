import numpy as np
from scipy import sparse

from fed_dp_lp.p5fc_data import (
    capped_stratified_positive_split,
    canonical_undirected_edges,
    feature_matrix_audit,
    load_graphsaint_adjacency,
    sample_stratified_nonedges,
    splitmix64,
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


def test_splitmix_and_capped_split_are_deterministic_and_disjoint():
    edges = np.asarray(
        [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3], [2, 4], [3, 5]]
    )
    homes = np.asarray([0, 0, 1, 1, 0, 1])
    first = capped_stratified_positive_split(
        edges, homes, seed=17, validation_cap=2, test_cap=2
    )
    second = capped_stratified_positive_split(
        edges, homes, seed=17, validation_cap=2, test_cap=2
    )
    assert all(np.array_equal(left, right) for left, right in zip(first, second))
    keys = [{tuple(edge) for edge in part} for part in first]
    assert not (keys[0] & keys[1] or keys[0] & keys[2] or keys[1] & keys[2])
    assert sum(len(part) for part in first) == len(edges)
    assert np.array_equal(
        splitmix64(np.arange(10), seed=3), splitmix64(np.arange(10), seed=3)
    )


def test_stratified_nonedges_match_counts_and_do_not_overlap_edges():
    edges = np.asarray([[0, 1], [0, 2], [1, 3], [2, 4], [3, 5]])
    homes = np.asarray([0, 0, 1, 1, 0, 1])
    validation, test = sample_stratified_nonedges(
        edges, homes, seed=29, validation_cap=2, test_cap=2
    )
    existing = {tuple(edge) for edge in edges}
    sampled = {tuple(edge) for edge in np.concatenate([validation, test])}
    assert len(validation) == len(test) == 2
    assert not existing & sampled
    assert len(sampled) == 4
    for values in (validation, test):
        cross = homes[values[:, 0]] != homes[values[:, 1]]
        assert cross.tolist().count(False) == cross.tolist().count(True) == 1
