import numpy as np

from fed_dp_lp.r5_holdout import (
    certification_mask,
    corrupted_pairs,
    finite_population_penalty,
    ranking_advantage,
)


EDGES = np.asarray([[0, 1], [0, 2], [1, 3], [2, 4], [3, 5]], dtype=np.int64)


def test_hash_partition_is_deterministic_and_order_invariant():
    mask = certification_mask(
        EDGES,
        nodes=6,
        dataset="toy",
        seed=17,
        salt="registered",
        probability=0.4,
    )
    permutation = np.asarray([3, 0, 4, 1, 2])
    shuffled = certification_mask(
        EDGES[permutation],
        nodes=6,
        dataset="toy",
        seed=17,
        salt="registered",
        probability=0.4,
    )
    assert np.array_equal(mask[permutation], shuffled)


def test_existing_assignments_are_stable_after_edge_insertion():
    original = certification_mask(
        EDGES,
        nodes=7,
        dataset="toy",
        seed=19,
        salt="registered",
        probability=0.5,
    )
    extended = certification_mask(
        np.row_stack([EDGES, [5, 6]]),
        nodes=7,
        dataset="toy",
        seed=19,
        salt="registered",
        probability=0.5,
    )
    assert np.array_equal(original, extended[:-1])


def test_corruption_is_deterministic_valid_and_graph_independent():
    first = corrupted_pairs(
        EDGES, nodes=6, dataset="toy", seed=23, salt="corruption"
    )
    second = corrupted_pairs(
        EDGES, nodes=6, dataset="toy", seed=23, salt="corruption"
    )
    assert np.array_equal(first, second)
    assert np.all(first[:, 0] != first[:, 1])
    assert all(tuple(pair) != tuple(edge) for pair, edge in zip(first, EDGES))


def test_ranking_advantage_and_finite_population_penalty():
    advantage = ranking_advantage(
        np.asarray([0.8, 0.2]),
        np.asarray([0.1, 0.3]),
        np.asarray([0.7, 0.5]),
        np.asarray([0.2, 0.4]),
    )
    assert np.array_equal(advantage, np.asarray([0.0, -1.0]))
    finite = finite_population_penalty(25, 100, failure_probability=0.03)
    infinite_population = np.sqrt(2.0 * np.log(1.0 / 0.03) / 25)
    assert 0.0 < finite < infinite_population
    assert np.isinf(
        finite_population_penalty(100, 100, failure_probability=0.03)
    )
