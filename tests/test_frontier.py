import numpy as np

from fed_dp_lp.frontier import (
    degree_upper_energy_ratio,
    effective_noise_std,
    expected_noise_energy,
    gaussian_norm_interval,
    signal_noise_energy_ratio,
)


def test_visible_message_noise_has_exact_k_energy_penalty():
    visible = expected_noise_energy(
        release_dimension=20,
        noise_std=2.0,
        clients=5,
        visibility="visible_messages",
    )
    ideal = expected_noise_energy(
        release_dimension=20,
        noise_std=2.0,
        clients=5,
        visibility="ideal_secagg",
    )
    assert np.isclose(visible / ideal, 5.0)
    assert np.isclose(
        effective_noise_std(2.0, clients=5, visibility="visible_messages"),
        2.0 * np.sqrt(5.0),
    )


def test_degree_bound_dominates_row_bounded_aggregation_ratio():
    encoded = np.asarray([[1.0, 0.0], [0.0, 1.0], [2**-0.5, 2**-0.5]])
    adjacency = np.asarray([[0, 1, 1], [1, 0, 0], [1, 0, 0]], dtype=float)
    signal = adjacency @ encoded
    observed = signal_noise_energy_ratio(
        signal, noise_std=1.0, clients=2, visibility="visible_messages"
    )
    upper = degree_upper_energy_ratio(
        adjacency.sum(axis=1),
        encoding_dimension=2,
        noise_std=1.0,
        clients=2,
        visibility="visible_messages",
    )
    assert observed <= upper + 1e-12


def test_gaussian_norm_interval_is_ordered_and_positive():
    lower, upper = gaussian_norm_interval(
        release_dimension=100,
        noise_std=1.0,
        clients=5,
        visibility="visible_messages",
        failure_probability=0.05,
    )
    assert 0 < lower < upper
