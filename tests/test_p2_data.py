import numpy as np
from scipy import sparse

from fed_dp_lp.p2_data import (
    balanced_sha256_homes,
    label_hash_subcells,
    public_coarsening,
    stratified_link_split,
)


def test_homes_are_deterministic_balanced_and_edge_independent():
    ids = tuple(str(index) for index in range(23))
    left = balanced_sha256_homes("fixture", ids, clients=5, seed=17)
    right = balanced_sha256_homes("fixture", ids, clients=5, seed=17)
    np.testing.assert_array_equal(left, right)
    sizes = np.bincount(left, minlength=5)
    assert sizes.max() - sizes.min() <= 1


def test_public_coarsening_is_deterministic():
    features = sparse.csr_matrix(np.eye(20, 5)[np.arange(20) % 5])
    left = public_coarsening(features, cells=4, components=3, random_state=7)
    right = public_coarsening(features, cells=4, components=3, random_state=7)
    np.testing.assert_array_equal(left, right)
    assert len(np.unique(left)) == 4


def test_label_hash_subcells_are_public_deterministic_and_balanced():
    ids = tuple(str(index) for index in range(32))
    labels = np.repeat([0, 1], 16)
    left = label_hash_subcells("fixture", ids, labels, subcells_per_label=4, seed=9)
    right = label_hash_subcells("fixture", ids, labels, subcells_per_label=4, seed=9)
    np.testing.assert_array_equal(left, right)
    assert len(np.unique(left)) == 8
    assert np.bincount(left).tolist() == [4] * 8


def test_stratified_split_is_disjoint_balanced_and_deterministic():
    nodes = 30
    homes = np.arange(nodes) % 3
    edges = np.asarray(
        [(u, v) for u in range(nodes) for v in range(u + 1, nodes) if (u + v) % 4 == 0]
    )
    left = stratified_link_split(edges, homes, seed=91)
    right = stratified_link_split(edges, homes, seed=91)
    for field in left.__dataclass_fields__:
        np.testing.assert_array_equal(getattr(left, field), getattr(right, field))

    positives = [left.train_positive, left.validation_positive, left.test_positive]
    positive_sets = [set(map(tuple, part)) for part in positives]
    assert not (positive_sets[0] & positive_sets[1])
    assert not (positive_sets[0] & positive_sets[2])
    assert not (positive_sets[1] & positive_sets[2])
    assert sum(map(len, positives)) == len(edges)
    assert len(left.train_positive) == len(left.train_negative)
    assert len(left.validation_positive) == len(left.validation_negative)
    assert len(left.test_positive) == len(left.test_negative)
    all_positive = set(map(tuple, edges))
    all_negative = set(
        map(
            tuple,
            np.concatenate(
                [left.train_negative, left.validation_negative, left.test_negative]
            ),
        )
    )
    assert not (all_positive & all_negative)
