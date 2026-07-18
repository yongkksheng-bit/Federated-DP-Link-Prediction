import numpy as np
import pytest

from fed_dp_lp.accounting import calibrate_gaussian, epsilon_from_rdp, gaussian_rdp


def test_gaussian_rdp_matches_closed_form_and_composes():
    orders = np.asarray([2.0, 8.0])
    observed = gaussian_rdp(orders, sensitivity=2.0, noise_std=4.0, steps=3)
    np.testing.assert_allclose(observed, 3 * orders * 4 / (2 * 16))


def test_calibration_meets_but_does_not_materially_overshoot_target():
    calibration = calibrate_gaussian(target_epsilon=4.0, delta=1e-6)
    assert calibration.epsilon <= 4.0
    smaller = gaussian_rdp(
        np.asarray(calibration.orders),
        sensitivity=1.0,
        noise_std=calibration.noise_std * 0.999,
    )
    epsilon, _ = epsilon_from_rdp(
        np.asarray(calibration.orders), smaller, delta=1e-6
    )
    assert epsilon > 4.0


@pytest.mark.parametrize("delta", [0.0, 1.0, -1e-6])
def test_invalid_delta_rejected(delta):
    with pytest.raises(ValueError):
        epsilon_from_rdp(np.asarray([2.0]), np.asarray([1.0]), delta=delta)
