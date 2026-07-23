import numpy as np

from fed_dp_lp.private_certificate import (
    CERTIFICATION_L2_SENSITIVITY,
    block_rademacher_sums,
    bounded_sum_count,
    certificate_lower_bound,
    one_sided_binomial_upper,
)


def test_sum_count_neighbor_change_is_bounded_by_sqrt_two():
    before = bounded_sum_count(np.array([-1.0, 0.25]))
    after = bounded_sum_count(np.array([-1.0, 0.25, 1.0]))
    assert np.isclose(np.linalg.norm(after - before), CERTIFICATION_L2_SENSITIVITY)


def test_certificate_rejects_small_count_and_returns_finite_valid_lower():
    invalid = certificate_lower_bound(
        np.array([2.0]),
        np.array([5.0]),
        coordinate_noise_std=1.0,
        beta_sum=0.01,
        beta_count=0.01,
        beta_sampling=0.03,
        dependence_factor=1,
        minimum_count_lower=50,
    )
    assert not invalid.valid[0]
    assert np.isneginf(invalid.lower_bound[0])

    valid = certificate_lower_bound(
        np.array([300.0]),
        np.array([1000.0]),
        coordinate_noise_std=1.0,
        beta_sum=0.01,
        beta_count=0.01,
        beta_sampling=0.03,
        dependence_factor=1,
        minimum_count_lower=50,
    )
    assert valid.valid[0]
    assert np.isfinite(valid.lower_bound[0])
    assert valid.lower_bound[0] < 0.3


def test_block_rademacher_is_deterministic_and_respects_blocks():
    first = block_rademacher_sums(
        np.random.default_rng(7),
        trials=20,
        count=100,
        dependence_factor=5,
        mean=0.1,
    )
    second = block_rademacher_sums(
        np.random.default_rng(7),
        trials=20,
        count=100,
        dependence_factor=5,
        mean=0.1,
    )
    np.testing.assert_array_equal(first, second)
    assert np.all(first % 5 == 0)


def test_binomial_upper_is_conservative_and_monotone():
    zero = one_sided_binomial_upper(0, 5000)
    ten = one_sided_binomial_upper(10, 5000)
    assert 0 < zero < ten < 0.01
