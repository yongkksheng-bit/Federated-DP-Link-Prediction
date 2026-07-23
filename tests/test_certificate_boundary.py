import math

import pytest

from fed_dp_lp.certificate_boundary import (
    CertificateBoundary,
    activation_power_lower_bound,
    aggregate_noise_std,
    minimum_certification_count,
    minimum_detectable_effect,
)


def boundary(noise: float = 0.0, dependence: float = 1.0) -> CertificateBoundary:
    return CertificateBoundary(
        gamma=0.02,
        beta_sum=0.01,
        beta_count=0.01,
        beta_sampling=0.03,
        beta_power=0.05,
        dependence_factor=dependence,
        minimum_count_lower=50,
        effective_noise_std=noise,
    )


def test_nonprivate_inverse_has_closed_form() -> None:
    count = 1200
    observed = minimum_detectable_effect(count, boundary())
    expected = 0.02 + math.sqrt(
        2 * math.log(1 / 0.05) / count
    ) + math.sqrt(2 * math.log(1 / 0.03) / count)
    assert observed == pytest.approx(expected)


def test_forward_inverse_boundary_is_consistent() -> None:
    current = boundary(noise=3.0)
    count = 5000
    effect = minimum_detectable_effect(count, current)
    assert activation_power_lower_bound(count, effect, current) == pytest.approx(
        current.gamma
    )


def test_minimum_count_is_exact_integer_transition() -> None:
    current = boundary(noise=2.0)
    count = minimum_certification_count(0.1, current, maximum_count=1_000_000)
    assert count is not None
    assert activation_power_lower_bound(count, 0.1, current) >= current.gamma
    assert activation_power_lower_bound(count - 1, 0.1, current) < current.gamma


def test_minimum_count_monotonicities() -> None:
    low_effect = minimum_certification_count(
        0.05, boundary(noise=2.0), maximum_count=10_000_000
    )
    high_effect = minimum_certification_count(
        0.1, boundary(noise=2.0), maximum_count=10_000_000
    )
    high_dependence = minimum_certification_count(
        0.1, boundary(noise=2.0, dependence=5.0), maximum_count=10_000_000
    )
    assert low_effect is not None and high_effect is not None
    assert high_dependence is not None
    assert high_effect <= low_effect
    assert high_dependence >= high_effect


def test_effect_at_or_below_gamma_has_no_finite_boundary() -> None:
    assert (
        minimum_certification_count(0.02, boundary(), maximum_count=10_000_000)
        is None
    )


def test_visibility_noise_scaling() -> None:
    assert aggregate_noise_std(
        2.0, clients=20, visibility="ideal_secagg"
    ) == pytest.approx(2.0)
    assert aggregate_noise_std(
        2.0, clients=20, visibility="visible_messages"
    ) == pytest.approx(2.0 * math.sqrt(20))
