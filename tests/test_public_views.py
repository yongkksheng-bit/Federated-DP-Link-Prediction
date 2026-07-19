import numpy as np

from fed_dp_lp.public_views import (
    balanced_labels,
    corrupt_groups,
    refine_groups,
    repartition_edges,
)


def test_corruption_changes_exact_count_and_never_keeps_selected_label():
    groups = np.arange(100) % 5
    changed = corrupt_groups(groups, 0.25, np.random.default_rng(3))
    assert np.sum(changed != groups) == 25


def test_refinement_is_nested_balanced_and_contiguous():
    groups = np.repeat(np.arange(3), 20)
    refined = refine_groups(groups, 4, np.random.default_rng(4))
    assert np.all(refined // 4 == groups)
    assert tuple(np.unique(refined)) == tuple(range(12))
    counts = np.bincount(refined)
    assert counts.max() - counts.min() <= 1


def test_repartition_preserves_each_edge_exactly_once():
    edges = np.asarray([[0, 1], [0, 2], [1, 3], [2, 3]], dtype=np.int64)
    homes = np.asarray([0, 1, 2, 0])
    parts = repartition_edges(edges, homes, clients=3)
    reconstructed = np.concatenate(parts, axis=0)
    assert sorted(map(tuple, reconstructed)) == sorted(map(tuple, edges))


def test_balanced_labels_are_deterministic():
    left = balanced_labels(60, 10, np.random.default_rng(8))
    right = balanced_labels(60, 10, np.random.default_rng(8))
    np.testing.assert_array_equal(left, right)
