import numpy as np
from scipy import sparse

from fed_dp_lp.conditioned_release import (
    canonical_pair_sample,
    conditioned_counts,
    conditioned_log_enrichment,
    cosine_bin_indices,
    public_capacity_layout,
    score_conditioned_pairs,
)


BIN_EDGES = np.asarray([0.0, 1e-12, 0.2, 1.0000001])


def test_cosine_bins_separate_zero_and_are_stable():
    scores = np.asarray([0.0, 1e-13, 1e-12, 0.1, 0.2, 1.0])
    assert cosine_bin_indices(scores, BIN_EDGES).tolist() == [0, 0, 1, 1, 2, 2]


def test_public_pair_sample_is_canonical_unique_and_deterministic():
    first = canonical_pair_sample(100, maximum_pairs=500, seed=17)
    second = canonical_pair_sample(100, maximum_pairs=500, seed=17)
    assert np.array_equal(first, second)
    assert np.all(first[:, 0] < first[:, 1])
    assert len(np.unique(first[:, 0] * 100 + first[:, 1])) == len(first)


def test_capacity_estimate_is_positive_and_sums_to_pair_universe():
    features = sparse.eye(8, format="csr")
    cells = np.repeat(np.arange(2), 4)
    layout = public_capacity_layout(
        features, cells, BIN_EDGES, maximum_pairs=10, seed=2
    )
    assert layout.dimension == 9
    assert np.all(layout.capacities > 0)
    assert np.isclose(np.sum(layout.capacities), 28.0)


def test_one_edge_changes_exactly_one_coordinate_with_l2_one():
    features = sparse.csr_matrix(
        [[1, 0], [1, 1], [0, 1], [1, 0]], dtype=np.float64
    )
    cells = np.asarray([0, 0, 1, 1])
    layout = public_capacity_layout(
        features, cells, BIN_EDGES, maximum_pairs=100, seed=2
    )
    empty = conditioned_counts(
        np.empty((0, 2), dtype=np.int64), cells, np.empty(0), layout
    )
    one = conditioned_counts(
        np.asarray([[0, 2]]), cells, np.asarray([0.0]), layout
    )
    difference = one - empty
    assert np.count_nonzero(difference) == 1
    assert np.linalg.norm(difference) == 1.0


def test_bounded_residual_and_inference_score():
    features = sparse.csr_matrix(
        [[1, 0], [1, 1], [0, 1], [1, 0]], dtype=np.float64
    )
    cells = np.asarray([0, 0, 1, 1])
    layout = public_capacity_layout(
        features, cells, BIN_EDGES, maximum_pairs=100, seed=2
    )
    counts = np.linspace(-10, 20, layout.dimension)
    residual = conditioned_log_enrichment(counts, layout, alpha=1.0, clip=4.0)
    assert np.max(np.abs(residual)) <= 1.0
    pairs = np.asarray([[0, 1], [0, 2], [2, 3]])
    public = np.asarray([0.0, 0.1, 1.0])
    scored = score_conditioned_pairs(
        public, pairs, cells, residual, layout, weight=0.05
    )
    assert scored.shape == public.shape
    assert np.max(np.abs(scored - public)) <= 0.05 + 1e-12
