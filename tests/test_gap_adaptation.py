import numpy as np
from scipy import sparse

from fed_dp_lp.gap_adaptation import (
    UNDIRECTED_EDGE_L2_SENSITIVITY,
    client_owned_edges,
    normalize_rows,
    public_svd_encoder,
    release_private_aggregations,
    score_pairs_from_channels,
    undirected_adjacency,
    undirected_sum_aggregation,
)


def test_undirected_edge_change_has_sqrt_two_sensitivity():
    features = normalize_rows(np.asarray([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]))
    changed = undirected_sum_aggregation(np.asarray([[0, 1]]), features)
    assert np.isclose(np.linalg.norm(changed), UNDIRECTED_EDGE_L2_SENSITIVITY)


def test_public_encoder_is_row_bounded_and_handles_zero_rows():
    features = sparse.csr_matrix([[1.0, 0.0, 2.0], [0.0, 0.0, 0.0], [0.0, 3.0, 1.0]])
    encoded = public_svd_encoder(features, dimension=2, random_state=7)
    assert encoded.shape == (3, 2)
    assert np.max(np.linalg.norm(encoded, axis=1)) <= 1.0 + 1e-12
    assert np.all(encoded[1] == 0)


def test_visible_release_and_postprocessed_scores_are_finite():
    features = normalize_rows(np.asarray([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]))
    edges = np.asarray([[0, 1], [1, 2]])
    homes = np.asarray([0, 1, 0])
    local = client_owned_edges(edges, homes, clients=2)
    adjacency = undirected_adjacency(local, len(features))
    channels = release_private_aggregations(
        local,
        features,
        hops=2,
        noise_std=1.0,
        visibility="visible_messages",
        rng=np.random.default_rng(8),
        adjacency=adjacency,
    )
    scores = score_pairs_from_channels(channels, np.asarray([[0, 1], [0, 2]]))
    assert len(channels) == 3
    assert np.all(np.isfinite(scores))
    assert np.max(np.abs(scores)) <= 1.0 + 1e-12


def test_csr_and_indexed_aggregations_match():
    features = normalize_rows(np.asarray([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]))
    local = (np.asarray([[0, 1]]), np.asarray([[1, 2]]))
    expected = sum(
        (undirected_sum_aggregation(edges, features) for edges in local),
        start=np.zeros_like(features),
    )
    observed = undirected_adjacency(local, len(features)) @ features
    assert np.allclose(observed, expected)
