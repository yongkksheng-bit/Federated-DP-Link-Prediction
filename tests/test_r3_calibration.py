import pytest

from scripts.run_r3_monte_carlo_calibration import (
    binomial_lower,
    rounded_count,
)


def test_binomial_lower_endpoints() -> None:
    assert binomial_lower(0, 100) == 0.0
    assert 0.9 < binomial_lower(100, 100) < 1.0


def test_rounded_count_respects_dependence_blocks() -> None:
    assert rounded_count(101.1, 5) == 105
    assert rounded_count(1.0, 5) == 5


def test_invalid_binomial_inputs_rejected() -> None:
    with pytest.raises(ValueError):
        binomial_lower(2, 1)
