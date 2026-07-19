import numpy as np

from fed_dp_lp.central_pair_dp import (
    EDGE_RECORD_MULTIPLICITY,
    bounded_pair_design,
    clipped_gradient_sum,
    stable_negative_pairs,
    train_private_logistic,
)
from fed_dp_lp.gap_adaptation import normalize_rows


def rows(values):
    return {tuple(row) for row in np.asarray(values).tolist()}


def test_stable_negatives_change_by_at_most_one_replacement():
    base = np.asarray([[0, 1], [2, 3]])
    negatives = stable_negative_pairs(8, base, count=12, seed=19)
    inserted = negatives[3]
    changed = np.row_stack([base, inserted])
    changed_negatives = stable_negative_pairs(8, changed, count=12, seed=19)
    assert len(rows(negatives) - rows(changed_negatives)) <= 1
    assert len(rows(changed_negatives) - rows(negatives)) <= 1
    assert EDGE_RECORD_MULTIPLICITY == 3


def test_pair_design_and_clipped_gradient_are_bounded():
    encoded = normalize_rows(np.random.default_rng(2).normal(size=(7, 4)))
    pairs = np.asarray([[0, 1], [2, 3], [4, 5]])
    design = bounded_pair_design(encoded, pairs)
    assert np.max(np.linalg.norm(design, axis=1)) <= 1.0 + 1e-12
    gradient = clipped_gradient_sum(
        design, np.asarray([1, 0, 1]), np.zeros(design.shape[1]), clip_norm=0.25
    )
    assert np.linalg.norm(gradient) <= 3 * 0.25 + 1e-12


def test_private_logistic_returns_finite_weights():
    encoded = normalize_rows(np.random.default_rng(4).normal(size=(8, 3)))
    pairs = np.asarray([[0, 1], [0, 2], [3, 4], [5, 6]])
    design = bounded_pair_design(encoded, pairs)
    weights = train_private_logistic(
        design,
        np.asarray([1, 1, 0, 0]),
        steps=3,
        learning_rate=0.2,
        clip_norm=1.0,
        noise_std=2.0,
        l2_penalty=1e-3,
        rng=np.random.default_rng(5),
    )
    assert weights.shape == (design.shape[1],)
    assert np.all(np.isfinite(weights))
