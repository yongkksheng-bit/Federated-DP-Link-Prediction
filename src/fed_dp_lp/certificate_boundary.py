"""High-probability power boundary for the private utility certificate."""

from __future__ import annotations

from dataclasses import dataclass
import math

from scipy.stats import norm


@dataclass(frozen=True)
class CertificateBoundary:
    gamma: float
    beta_sum: float
    beta_count: float
    beta_sampling: float
    beta_power: float
    dependence_factor: float
    minimum_count_lower: float
    effective_noise_std: float

    def __post_init__(self) -> None:
        if not 0 <= self.gamma < 1:
            raise ValueError("gamma must lie in [0, 1)")
        if any(
            not 0 < value < 1
            for value in (
                self.beta_sum,
                self.beta_count,
                self.beta_sampling,
                self.beta_power,
            )
        ):
            raise ValueError("failure probabilities must lie in (0, 1)")
        if self.dependence_factor < 1:
            raise ValueError("dependence_factor must be at least one")
        if self.minimum_count_lower <= 0:
            raise ValueError("minimum_count_lower must be positive")
        if self.effective_noise_std < 0:
            raise ValueError("effective_noise_std cannot be negative")

    @property
    def sum_noise_radius(self) -> float:
        return float(
            self.effective_noise_std * norm.ppf(1.0 - self.beta_sum / 2.0)
        )

    @property
    def count_noise_radius(self) -> float:
        return float(
            self.effective_noise_std * norm.ppf(1.0 - self.beta_count / 2.0)
        )


def aggregate_noise_std(
    client_noise_std: float, *, clients: int, visibility: str
) -> float:
    """Return the server-side aggregate standard deviation."""
    if client_noise_std < 0 or clients <= 0:
        raise ValueError("invalid noise standard deviation or client count")
    if visibility == "ideal_secagg":
        return float(client_noise_std)
    if visibility == "visible_messages":
        return float(client_noise_std * math.sqrt(clients))
    raise ValueError(f"unsupported visibility model: {visibility}")


def _sampling_radius(
    count: float, *, beta: float, dependence_factor: float
) -> float:
    if count <= 0:
        return math.inf
    return math.sqrt(
        2.0 * dependence_factor * math.log(1.0 / beta) / count
    )


def activation_power_lower_bound(
    count: int, population_effect: float, boundary: CertificateBoundary
) -> float:
    """Return the theorem-guaranteed lower certificate on the power event."""
    if count <= 0 or not 0 <= population_effect <= 1:
        raise ValueError("invalid count or population effect")
    sum_radius = boundary.sum_noise_radius
    count_radius = boundary.count_noise_radius
    count_lower = count - 2.0 * count_radius
    if count_lower < boundary.minimum_count_lower:
        return -math.inf
    power_radius = _sampling_radius(
        count,
        beta=boundary.beta_power,
        dependence_factor=boundary.dependence_factor,
    )
    numerator = count * (population_effect - power_radius) - 2.0 * sum_radius
    if numerator <= 0:
        return -math.inf
    ratio = numerator / (count + 2.0 * count_radius)
    validity_radius = _sampling_radius(
        count_lower,
        beta=boundary.beta_sampling,
        dependence_factor=boundary.dependence_factor,
    )
    return float(ratio - validity_radius)


def minimum_detectable_effect(
    count: int, boundary: CertificateBoundary
) -> float:
    """Return the smallest population effect satisfying the power inequality."""
    if count <= 0:
        raise ValueError("count must be positive")
    sum_radius = boundary.sum_noise_radius
    count_radius = boundary.count_noise_radius
    count_lower = count - 2.0 * count_radius
    if count_lower < boundary.minimum_count_lower:
        return math.inf
    power_radius = _sampling_radius(
        count,
        beta=boundary.beta_power,
        dependence_factor=boundary.dependence_factor,
    )
    validity_radius = _sampling_radius(
        count_lower,
        beta=boundary.beta_sampling,
        dependence_factor=boundary.dependence_factor,
    )
    return float(
        power_radius
        + (
            2.0 * sum_radius
            + (count + 2.0 * count_radius)
            * (boundary.gamma + validity_radius)
        )
        / count
    )


def minimum_certification_count(
    population_effect: float,
    boundary: CertificateBoundary,
    *,
    maximum_count: int,
) -> int | None:
    """Find the exact smallest integer count satisfying the sufficient bound."""
    if not 0 <= population_effect <= 1 or maximum_count <= 0:
        raise ValueError("invalid population effect or maximum count")
    if population_effect <= boundary.gamma:
        return None

    count_radius = boundary.count_noise_radius
    first_valid = max(
        1,
        math.ceil(2.0 * count_radius + boundary.minimum_count_lower),
    )
    if first_valid > maximum_count:
        return None

    def passes(count: int) -> bool:
        return (
            activation_power_lower_bound(count, population_effect, boundary)
            >= boundary.gamma
        )

    if passes(first_valid):
        return first_valid

    low = first_valid
    high = first_valid
    while high < maximum_count:
        low = high
        high = min(maximum_count, high * 2)
        if passes(high):
            break
    if not passes(high):
        return None

    while low + 1 < high:
        middle = (low + high) // 2
        if passes(middle):
            high = middle
        else:
            low = middle
    return high
