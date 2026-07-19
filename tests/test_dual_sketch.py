import numpy as np

from fed_dp_lp.dual_sketch import (
    joint_public_query,
    public_rademacher_signatures,
    score_dual_sketch_pairs,
)
from fed_dp_lp.gap_adaptation import normalize_rows, undirected_sum_aggregation


def test_joint_query_rows_are_bounded_by_one():
    semantic = normalize_rows(np.random.default_rng(1).normal(size=(12, 4)))
    topology = public_rademacher_signatures(12, dimension=8, seed=2)
    joint = joint_public_query(semantic, topology, semantic_fraction=0.4)
    assert joint.shape == (12, 12)
    assert np.max(np.linalg.norm(joint, axis=1)) <= 1.0 + 1e-12


def test_topology_dot_approximates_common_neighbors_at_large_dimension():
    edges = np.asarray([[0, 2], [0, 3], [1, 2], [1, 3], [1, 4]])
    signatures = public_rademacher_signatures(5, dimension=8192, seed=3)
    aggregated = undirected_sum_aggregation(edges, signatures)
    observed = float(aggregated[0] @ aggregated[1])
    assert abs(observed - 2.0) < 0.08


def test_dual_decoder_is_bounded_and_finite():
    rng = np.random.default_rng(4)
    released = rng.normal(size=(6, 10))
    pairs = np.asarray([[0, 1], [2, 3], [4, 5]])
    scores = score_dual_sketch_pairs(
        np.asarray([0.2, 0.5, 0.8]),
        released,
        pairs,
        semantic_dimension=4,
        mode="noise_standardized_dot",
        effective_noise_std=2.0,
        public_weight=1.0,
        semantic_weight=1.0,
        topology_weight=1.0,
    )
    assert np.all(np.isfinite(scores))
    assert np.max(np.abs(scores)) <= 1.0 + 1e-12
