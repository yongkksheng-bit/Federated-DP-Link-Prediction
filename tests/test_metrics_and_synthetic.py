import numpy as np

from fed_dp_lp.metrics import average_precision, roc_auc
from fed_dp_lp.synthetic import generate_sbm
from fed_dp_lp.generalized_synthetic import generate_reciprocal_preference_graph


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


def test_average_precision_handles_perfect_ranking():
    labels = np.asarray([0, 1, 0, 1])
    scores = np.asarray([0.1, 0.8, 0.2, 0.9])
    assert average_precision(labels, scores) == 1.0


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


def test_reciprocal_preference_generation_is_deterministic():
    config = dict(
        nodes=40,
        cells_count=4,
        clients=5,
        base_probability=0.02,
        one_sided_boost=0.08,
        mutual_boost=0.12,
        train_retention=0.7,
        feature_corruption=0.2,
    )
    left = generate_reciprocal_preference_graph(seed=9, **config)
    right = generate_reciprocal_preference_graph(seed=9, **config)
    np.testing.assert_array_equal(left.public_cells, right.public_cells)
    np.testing.assert_array_equal(left.latent_preferences, right.latent_preferences)
    for first, second in zip(left.client_edges, right.client_edges):
        np.testing.assert_array_equal(first, second)
