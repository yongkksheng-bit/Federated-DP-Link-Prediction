"""Necessary sample bounds for bounded private utility certification."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class TestingLowerBound:
    nonprivate_count: float
    private_count: float
    combined_count: float
    replacement_epsilon: float
    replacement_delta: float
    required_hamming_distance: float
    dp_root_residual: float


def bernoulli_kl(p: float, q: float) -> float:
    """Return KL(Ber(p) || Ber(q))."""
    if not 0 < p < 1 or not 0 < q < 1:
        raise ValueError("Bernoulli probabilities must lie in (0, 1)")
    return float(
        p * math.log(p / q)
        + (1.0 - p) * math.log((1.0 - p) / (1.0 - q))
    )


def replacement_privacy_from_unbounded(
    epsilon: float, delta: float
) -> tuple[float, float]:
    """Convert add/remove DP to replacement DP by two-step group privacy."""
    if epsilon < 0 or not 0 <= delta < 1:
        raise ValueError("invalid privacy parameters")
    return 2.0 * epsilon, (1.0 + math.exp(epsilon)) * delta


def nonprivate_certification_count_lower_bound(
    *,
    null_mean: float,
    effect_gap: float,
    maximum_error: float,
    dependence_factor: float,
) -> float:
    """Le Cam/Pinsker necessary count for the block-Rademacher hard pair."""
    if (
        not -1 < null_mean < 1
        or effect_gap <= 0
        or null_mean + effect_gap >= 1
        or not 0 < maximum_error < 0.5
        or dependence_factor < 1
    ):
        raise ValueError("invalid testing parameters")
    p0 = (1.0 + null_mean) / 2.0
    p1 = (1.0 + null_mean + effect_gap) / 2.0
    divergence = bernoulli_kl(p0, p1)
    return float(
        dependence_factor
        * 2.0
        * (1.0 - 2.0 * maximum_error) ** 2
        / divergence
    )


def private_lecam_expression(
    hamming_distance: float,
    *,
    replacement_epsilon: float,
    replacement_delta: float,
) -> float:
    """Privacy term inside the Acharya-Sun-Zhang DP Le Cam bound."""
    if (
        hamming_distance < 0
        or replacement_epsilon < 0
        or replacement_delta < 0
    ):
        raise ValueError("invalid DP Le Cam parameters")
    return float(
        0.9
        * math.exp(-10.0 * replacement_epsilon * hamming_distance)
        - 10.0 * hamming_distance * replacement_delta
    )


def required_hamming_distance(
    *,
    replacement_epsilon: float,
    replacement_delta: float,
    maximum_error: float,
    tolerance: float = 1e-12,
    maximum_distance: float = 1e12,
) -> tuple[float, float]:
    """Solve the monotone DP Le Cam privacy inequality at equality."""
    if (
        replacement_epsilon < 0
        or replacement_delta < 0
        or not 0 < maximum_error < 0.45
        or tolerance <= 0
        or maximum_distance <= 0
    ):
        raise ValueError("invalid root parameters")
    target = 2.0 * maximum_error

    def residual(distance: float) -> float:
        return private_lecam_expression(
            distance,
            replacement_epsilon=replacement_epsilon,
            replacement_delta=replacement_delta,
        ) - target

    low = 0.0
    high = 1.0
    while residual(high) > 0.0 and high < maximum_distance:
        high = min(maximum_distance, high * 2.0)
    if residual(high) > 0.0:
        raise RuntimeError("DP Le Cam root exceeds maximum_distance")

    for _ in range(300):
        middle = (low + high) / 2.0
        if residual(middle) > 0.0:
            low = middle
        else:
            high = middle
        if high - low <= tolerance * max(1.0, high):
            break
    root = high
    return float(root), abs(float(residual(root)))


def certification_count_lower_bound(
    *,
    null_mean: float,
    effect_gap: float,
    maximum_error: float,
    dependence_factor: float,
    unbounded_epsilon: float,
    unbounded_delta: float,
    root_tolerance: float = 1e-12,
) -> TestingLowerBound:
    """Combine non-private and general central-DP necessary conditions."""
    nonprivate = nonprivate_certification_count_lower_bound(
        null_mean=null_mean,
        effect_gap=effect_gap,
        maximum_error=maximum_error,
        dependence_factor=dependence_factor,
    )
    replacement_epsilon, replacement_delta = replacement_privacy_from_unbounded(
        unbounded_epsilon, unbounded_delta
    )
    distance, residual = required_hamming_distance(
        replacement_epsilon=replacement_epsilon,
        replacement_delta=replacement_delta,
        maximum_error=maximum_error,
        tolerance=root_tolerance,
    )
    private = 2.0 * distance / effect_gap
    return TestingLowerBound(
        nonprivate_count=nonprivate,
        private_count=private,
        combined_count=max(nonprivate, private),
        replacement_epsilon=replacement_epsilon,
        replacement_delta=replacement_delta,
        required_hamming_distance=distance,
        dp_root_residual=residual,
    )
