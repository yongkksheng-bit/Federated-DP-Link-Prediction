import numpy as np

from fed_dp_lp.metrics import roc_auc
from fed_dp_lp.synthetic import generate_sbm


CONFIG = {
    "nodes": 40,
    "groups_count": 4,
    "clients": 5,
    "within_probability": 0.2,
    "between_probability": 0.03,
    "train_retention": 0.7,
}


def test_auc_handles_ties_and_perfect_ranking():
    assert roc_auc(np.asarray([1, 1, 0, 0]), np.asarray([1.0, 1.0, 0.0, 0.0])) == 1.0
    assert roc_auc(np.asarray([1, 0]), np.asarray([0.0, 0.0])) == 0.5


def test_synthetic_generation_is_deterministic_and_edges_are_unique():
    left = generate_sbm(seed=7, **CONFIG)
    right = generate_sbm(seed=7, **CONFIG)
    np.testing.assert_array_equal(left.groups, right.groups)
    np.testing.assert_array_equal(left.homes, right.homes)
    for first, second in zip(left.client_edges, right.client_edges):
        np.testing.assert_array_equal(first, second)
    all_edges = np.concatenate(left.client_edges, axis=0)
    assert len(np.unique(all_edges, axis=0)) == len(all_edges)
    assert np.all(all_edges[:, 0] < all_edges[:, 1])
