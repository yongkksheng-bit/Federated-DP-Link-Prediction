import numpy as np

from fed_dp_lp.certfed_synthetic import (
    corrupted_pairs,
    generate_sbm_graph,
    pairwise_advantages,
    partition_edges,
    release_certification_query,
    release_training_channels,
)


def test_synthetic_graph_partition_is_disjoint_and_deterministic():
    graph = generate_sbm_graph(
        nodes=80,
        communities=4,
        clients=5,
        p_in=0.2,
        p_out=0.02,
        feature_noise=0.5,
        seed=7,
    )
    first = partition_edges(
        graph.edges,
        nodes=80,
        seed=9,
        training_fraction=0.6,
        certification_fraction=0.2,
    )
    second = partition_edges(
        graph.edges,
        nodes=80,
        seed=9,
        training_fraction=0.6,
        certification_fraction=0.2,
    )
    assert all(np.array_equal(a, b) for a, b in zip(first, second))
    sets = [{tuple(edge) for edge in part} for part in first]
    assert not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
    assert sum(map(len, first)) == len(graph.edges)


def test_corruption_avoids_endpoints_without_graph_rejection():
    edges = np.array([[0, 1], [2, 4], [3, 5]])
    corrupted = corrupted_pairs(edges, nodes=8, seed=11)
    assert np.all(corrupted[:, 0] < corrupted[:, 1])
    for edge, pair in zip(edges, corrupted):
        assert tuple(pair) != tuple(edge)


def test_visible_training_and_certificate_transcripts_aggregate_exactly():
    graph = generate_sbm_graph(
        nodes=40,
        communities=4,
        clients=5,
        p_in=0.3,
        p_out=0.03,
        feature_noise=0.2,
        seed=4,
    )
    release = release_training_channels(
        graph.edges,
        graph.features,
        graph.homes,
        clients=5,
        noise_std=1.0,
        visibility="visible_messages",
        rng=np.random.default_rng(5),
    )
    assert release.message_count == 5
    assert release.aggregate_error <= 1e-12
    comparisons = corrupted_pairs(graph.edges, nodes=40, seed=8)
    advantage = pairwise_advantages(
        (graph.features,), release.channels, graph.edges, comparisons
    )
    query = release_certification_query(
        advantage,
        graph.homes[graph.edges[:, 0]],
        clients=5,
        noise_std=1.0,
        visibility="visible_messages",
        rng=np.random.default_rng(6),
    )
    assert query.message_count == 5
    assert query.aggregate_error <= 1e-12
