"""Private target-domain utility certificate from a noisy sum and count."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import beta, norm


CERTIFICATION_L2_SENSITIVITY = np.sqrt(2.0)


@dataclass(frozen=True)
class CertificateResult:
    lower_bound: np.ndarray
    valid: np.ndarray
    sum_noise_bound: float
    count_noise_bound: float


def bounded_sum_count(values: np.ndarray) -> np.ndarray:
    """Return (sum, count) for contributions in [-1,1]."""
    contributions = np.asarray(values, dtype=np.float64)
    if contributions.ndim != 1 or np.any(np.abs(contributions) > 1.0):
        raise ValueError("certificate contributions must be one-dimensional in [-1,1]")
    return np.asarray([contributions.sum(), len(contributions)], dtype=np.float64)


def certificate_lower_bound(
    noisy_sum: np.ndarray,
    noisy_count: np.ndarray,
    *,
    coordinate_noise_std: float,
    beta_sum: float,
    beta_count: float,
    beta_sampling: float,
    dependence_factor: float,
    minimum_count_lower: float,
) -> CertificateResult:
    """Compute the R1 one-sided population utility lower certificate."""
    if coordinate_noise_std <= 0 or dependence_factor < 1:
        raise ValueError("invalid noise or dependence factor")
    if any(not 0 < value < 1 for value in (beta_sum, beta_count, beta_sampling)):
        raise ValueError("failure allocations must lie in (0,1)")
    if minimum_count_lower <= 0:
        raise ValueError("minimum count lower bound must be positive")
    sums = np.asarray(noisy_sum, dtype=np.float64)
    counts = np.asarray(noisy_count, dtype=np.float64)
    if sums.shape != counts.shape:
        raise ValueError("noisy sum and count must have identical shapes")

    sum_bound = float(coordinate_noise_std * norm.ppf(1.0 - beta_sum / 2.0))
    count_bound = float(
        coordinate_noise_std * norm.ppf(1.0 - beta_count / 2.0)
    )
    sum_lower = sums - sum_bound
    count_lower = counts - count_bound
    count_upper = counts + count_bound
    valid = (
        (sum_lower > 0.0)
        & (count_lower >= minimum_count_lower)
        & (count_upper > 0.0)
    )
    lower = np.full(sums.shape, -np.inf, dtype=np.float64)
    empirical = np.divide(
        sum_lower,
        count_upper,
        out=np.zeros_like(sums),
        where=count_upper > 0.0,
    )
    sampling = np.sqrt(
        2.0
        * dependence_factor
        * np.log(1.0 / beta_sampling)
        / np.maximum(count_lower, np.finfo(np.float64).tiny)
    )
    lower[valid] = empirical[valid] - sampling[valid]
    return CertificateResult(
        lower_bound=lower,
        valid=valid,
        sum_noise_bound=sum_bound,
        count_noise_bound=count_bound,
    )


def one_sided_binomial_upper(
    successes: int, trials: int, *, confidence: float = 0.95
) -> float:
    """Clopper-Pearson one-sided upper confidence limit."""
    if trials <= 0 or not 0 <= successes <= trials or not 0 < confidence < 1:
        raise ValueError("invalid binomial confidence inputs")
    if successes == trials:
        return 1.0
    return float(beta.ppf(confidence, successes + 1, trials - successes))


def block_rademacher_sums(
    rng: np.random.Generator,
    *,
    trials: int,
    count: int,
    dependence_factor: int,
    mean: float,
) -> np.ndarray:
    """Sample sums of block-replicated {-1,+1} contributions."""
    if (
        trials <= 0
        or count <= 0
        or dependence_factor <= 0
        or count % dependence_factor
        or not -1.0 <= mean <= 1.0
    ):
        raise ValueError("invalid block-Rademacher parameters")
    blocks = count // dependence_factor
    positive = rng.binomial(blocks, (1.0 + mean) / 2.0, size=trials)
    return dependence_factor * (2.0 * positive - blocks)
