import numpy as np
from scipy import sparse

from fed_dp_lp.gap_adaptation import normalize_rows
from fed_dp_lp.reciprocal_profile import (
    RAP_L2_SENSITIVITY,
    joint_profile_scales,
    reciprocal_profile_counts,
    reciprocal_profile_scores,
    release_joint_semantic_profile,
)


def test_one_edge_changes_two_profile_coordinates():
    cells = np.asarray([0, 1, 1])
    counts = reciprocal_profile_counts(
        np.asarray([[0, 2]]), cells, node_count=3
    )
    assert counts[0, 1] == 1
    assert counts[2, 0] == 1
    assert np.sum(counts) == 2
    assert np.isclose(np.linalg.norm(counts), RAP_L2_SENSITIVITY)


def test_joint_semantic_profile_sensitivity_is_sqrt_two():
    encoded = normalize_rows(np.asarray([[1.0, 0.0], [0.0, 1.0]]))
    semantic_change = np.asarray([[0.0, 1.0], [1.0, 0.0]])
    profile_change = np.eye(2)
    for gamma in (0.01, 0.1, 0.5):
        semantic_scale, profile_scale = joint_profile_scales(gamma)
        squared = (
            np.linalg.norm(semantic_scale * semantic_change) ** 2
            + np.linalg.norm(profile_scale * profile_change) ** 2
        )
        assert np.isclose(np.sqrt(squared), RAP_L2_SENSITIVITY)


def test_joint_release_shapes_are_finite():
    adjacency = sparse.csr_matrix([[0.0, 1.0], [1.0, 0.0]])
    semantic, profile = release_joint_semantic_profile(
        adjacency,
        np.eye(2),
        (np.eye(2), np.zeros((2, 2))),
        profile_energy_fraction=0.1,
        noise_std=1.0,
        visibility="visible_messages",
        rng=np.random.default_rng(7),
    )
    assert semantic.shape == (2, 2)
    assert profile.shape == (2, 2)
    assert np.all(np.isfinite(semantic))
    assert np.all(np.isfinite(profile))


def test_reciprocal_score_rewards_mutual_cell_preference():
    profiles = np.asarray([[0.0, 8.0], [7.0, 0.0], [8.0, 0.0]])
    cells = np.asarray([0, 1, 1])
    pairs = np.asarray([[0, 1], [1, 2]])
    scores = reciprocal_profile_scores(
        profiles,
        pairs,
        cells,
        prior_strength=1.0,
        effective_noise_std=0.0,
    )
    assert scores[0] > scores[1]
