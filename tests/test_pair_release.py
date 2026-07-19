import numpy as np

from fed_dp_lp.pair_release import (
    fit_public_ridge,
    normalize_rows,
    release_pair_statistic,
    symmetric_pair_features,
)


def test_pair_feature_norm_is_bounded_by_one():
    features = normalize_rows(np.random.default_rng(2).normal(size=(20, 5)))
    pairs = np.asarray([(u, v) for u in range(20) for v in range(u + 1, 20)])
    norms = np.linalg.norm(symmetric_pair_features(features, pairs), axis=1)
    assert np.max(norms) <= 1.0 + 1e-12


def test_add_remove_statistic_sensitivity_is_bounded_by_one():
    features = normalize_rows(np.random.default_rng(3).normal(size=(4, 3)))
    edge = np.asarray([[0, 2]])
    change = symmetric_pair_features(features, edge)[0]
    assert np.linalg.norm(change) <= 1.0 + 1e-12


def test_release_and_public_ridge_shapes():
    features = normalize_rows(np.random.default_rng(4).normal(size=(5, 3)))
    clients = (np.asarray([[0, 1], [1, 2]]), np.asarray([[3, 4]]))
    released = release_pair_statistic(
        clients, features, noise_std=1.0, visibility="ideal_secagg",
        rng=np.random.default_rng(5),
    )
    pairs = np.asarray([(u, v) for u in range(5) for v in range(u + 1, 5)])
    design = symmetric_pair_features(features, pairs)
    weights = fit_public_ridge(design, released)
    assert released.shape == (6,)
    assert weights.shape == (6,)
