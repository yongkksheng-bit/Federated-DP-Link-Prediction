import networkx as nx
import numpy as np
from scipy import sparse

from fed_dp_lp.dataset_properties import (
    common_neighbor_scores,
    degree_gini,
    public_descriptor_properties,
    sampled_average_clustering,
    topology_properties,
    training_adjacency,
)


def test_degree_gini_handles_regular_and_concentrated_degrees():
    assert degree_gini(np.ones(4)) == 0.0
    assert np.isclose(degree_gini(np.array([0.0, 0.0, 0.0, 4.0])), 0.75)


def test_adjacency_and_common_neighbors():
    edges = np.array([[0, 1], [0, 2], [1, 2], [2, 3]])
    adjacency = training_adjacency(4, edges)
    scores = common_neighbor_scores(adjacency, np.array([[0, 1], [0, 3]]))
    assert np.array_equal(scores, np.array([1.0, 1.0]))
    assert adjacency.nnz == 8


def test_sampled_clustering_is_deterministic():
    graph = nx.complete_graph(8)
    assert sampled_average_clustering(graph, node_cap=4, seed=7) == 1.0
    assert sampled_average_clustering(graph, node_cap=4, seed=7) == 1.0


def test_topology_and_descriptor_properties_are_finite():
    edges = np.array([[0, 1], [0, 2], [1, 2], [2, 3]])
    properties, _ = topology_properties(
        4,
        edges,
        np.array([0, 0, 1, 1]),
        clustering_node_cap=4,
        clustering_seed=3,
        louvain_resolution=1.0,
        louvain_seed=4,
    )
    assert properties["mean_degree"] == 2.0
    assert properties["largest_component_fraction"] == 1.0
    assert properties["cross_client_edge_fraction"] == 0.5
    assert all(np.isfinite(value) for value in properties.values())

    features = sparse.csr_matrix([[1, 0], [0, 0], [1, 1]])
    descriptors = public_descriptor_properties(features)
    assert np.isclose(descriptors["public_feature_coverage"], 2 / 3)
    assert descriptors["public_feature_density"] == 0.5
