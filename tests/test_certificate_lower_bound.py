import math

import pytest

from fed_dp_lp.certificate_lower_bound import (
    bernoulli_kl,
    nonprivate_certification_count_lower_bound,
    private_lecam_expression,
    replacement_privacy_from_unbounded,
    required_hamming_distance,
    certification_count_lower_bound,
)


def test_bernoulli_kl_is_positive_and_zero_on_identity() -> None:
    assert bernoulli_kl(0.5, 0.6) > 0
    assert bernoulli_kl(0.5, 0.5) == pytest.approx(0.0)


def test_dependence_multiplies_nonprivate_lower_bound() -> None:
    independent = nonprivate_certification_count_lower_bound(
        null_mean=0.02,
        effect_gap=0.08,
        maximum_error=0.05,
        dependence_factor=1,
    )
    dependent = nonprivate_certification_count_lower_bound(
        null_mean=0.02,
        effect_gap=0.08,
        maximum_error=0.05,
        dependence_factor=5,
    )
    assert dependent == pytest.approx(5 * independent)


def test_add_remove_to_replacement_conversion() -> None:
    epsilon, delta = replacement_privacy_from_unbounded(1.0, 1e-6)
    assert epsilon == 2.0
    assert delta == pytest.approx((1 + math.e) * 1e-6)


def test_pure_dp_root_matches_closed_form() -> None:
    epsilon = 2.0
    error = 0.05
    root, residual = required_hamming_distance(
        replacement_epsilon=epsilon,
        replacement_delta=0.0,
        maximum_error=error,
    )
    expected = math.log(0.9 / (2 * error)) / (10 * epsilon)
    assert root == pytest.approx(expected, rel=1e-10)
    assert residual <= 1e-12


def test_approximate_dp_root_hits_registered_equation() -> None:
    root, residual = required_hamming_distance(
        replacement_epsilon=2.0,
        replacement_delta=4e-6,
        maximum_error=0.05,
    )
    value = private_lecam_expression(
        root,
        replacement_epsilon=2.0,
        replacement_delta=4e-6,
    )
    assert value <= 0.1 + 1e-12
    assert residual <= 1e-10


def test_combined_bound_is_at_least_each_component() -> None:
    result = certification_count_lower_bound(
        null_mean=0.02,
        effect_gap=0.08,
        maximum_error=0.05,
        dependence_factor=1,
        unbounded_epsilon=1.0,
        unbounded_delta=1e-6,
    )
    assert result.combined_count >= result.nonprivate_count
    assert result.combined_count >= result.private_count
