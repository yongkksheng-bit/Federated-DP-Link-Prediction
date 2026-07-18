import numpy as np

from fed_dp_lp.block_release import (
    block_counts,
    make_block_layout,
    release_block_densities,
    score_pairs,
)


def test_add_remove_edge_sensitivity_is_exactly_one():
    groups = np.asarray([0, 0, 1, 1])
    layout = make_block_layout(groups)
    first = np.asarray([[0, 2]], dtype=np.int64)
    neighbor = np.asarray([[0, 2], [1, 3]], dtype=np.int64)
    delta = block_counts(neighbor, groups, layout) - block_counts(first, groups, layout)
    assert np.linalg.norm(delta, ord=2) == 1.0


def test_visible_messages_has_k_fold_noise_variance():
    groups = np.asarray([0, 0, 1, 1])
    clients = tuple(np.empty((0, 2), dtype=np.int64) for _ in range(4))
    visible = []
    aggregate = []
    for seed in range(4000):
        rng = np.random.default_rng(seed)
        visible.append(
            release_block_densities(
                clients,
                groups,
                noise_std=2.0,
                visibility="visible_messages",
                rng=rng,
            )[0][0]
        )
        rng = np.random.default_rng(seed)
        aggregate.append(
            release_block_densities(
                clients,
                groups,
                noise_std=2.0,
                visibility="ideal_secagg",
                rng=rng,
            )[0][0]
        )
    ratio = np.var(visible) / np.var(aggregate)
    assert 3.6 < ratio < 4.4


def test_inference_uses_only_release_and_public_inputs():
    groups = np.asarray([0, 0, 1, 1])
    layout = make_block_layout(groups)
    densities = np.asarray([0.8, 0.2, 0.7])
    pairs = np.asarray([[0, 1], [0, 2], [2, 3]])
    np.testing.assert_allclose(
        score_pairs(pairs, groups, densities, layout), [0.8, 0.2, 0.7]
    )
