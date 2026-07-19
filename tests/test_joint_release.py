import numpy as np
from scipy import sparse

from fed_dp_lp.joint_release import (
    JOINT_L2_SENSITIVITY,
    joint_scales,
    release_joint_first_hop,
    score_joint_release_pairs,
)
from fed_dp_lp.conditioned_release import ConditionedLayout
from fed_dp_lp.gap_adaptation import normalize_rows


def test_joint_edge_change_has_constant_sqrt_two_sensitivity():
    features = normalize_rows(np.asarray([[1.0, 0.0], [0.0, 1.0]]))
    edge_aggregation = np.asarray([[0.0, 1.0], [1.0, 0.0]])
    for gamma in (0.025, 0.1, 0.4):
        aggregation_scale, histogram_scale = joint_scales(gamma)
        change_squared = (
            np.linalg.norm(aggregation_scale * edge_aggregation) ** 2
            + histogram_scale**2
        )
        assert np.isclose(np.sqrt(change_squared), JOINT_L2_SENSITIVITY)


def test_joint_release_shapes_and_finite_values():
    adjacency = sparse.csr_matrix([[0.0, 1.0], [1.0, 0.0]])
    encoded = np.eye(2)
    local_counts = (np.asarray([1.0, 0.0]), np.asarray([0.0, 1.0]))
    aggregation, histogram = release_joint_first_hop(
        adjacency,
        encoded,
        local_counts,
        histogram_energy_fraction=0.2,
        noise_std=1.0,
        visibility="visible_messages",
        rng=np.random.default_rng(2),
    )
    assert aggregation.shape == (2, 2)
    assert histogram.shape == (2,)
    assert np.all(np.isfinite(aggregation))
    assert np.all(np.isfinite(histogram))


def test_joint_decoder_uses_public_score_to_select_histogram_bin():
    layout = ConditionedLayout(
        cell_pairs=((0, 0),),
        bin_edges=(0.0, 0.5, 1.0000001),
        capacities=np.ones(2),
        pair_to_index={(0, 0): 0},
    )
    channels = (np.asarray([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]]),)
    pairs = np.asarray([[0, 1], [0, 2]])
    public_scores = np.asarray([0.8, 0.2])
    scores = score_joint_release_pairs(
        channels,
        public_scores,
        pairs,
        np.zeros(3, dtype=np.int64),
        np.asarray([-0.5, 0.5]),
        layout,
        residual_weight=0.2,
    )
    # GAP scores are 1 and 0; high and low public-score bins add opposite residuals.
    assert np.allclose(scores, np.asarray([1.1, -0.1]))
