"""Small, explicit RDP accountant for fixed-sensitivity Gaussian releases."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


DEFAULT_ORDERS = np.asarray(
    [1.25, 1.5, 1.75, *range(2, 65), 128, 256], dtype=np.float64
)


@dataclass(frozen=True)
class GaussianCalibration:
    epsilon: float
    delta: float
    sensitivity: float
    noise_std: float
    steps: int
    selected_order: float
    orders: tuple[float, ...]
    rdp: tuple[float, ...]


def _validate_orders(orders: np.ndarray) -> None:
    if orders.ndim != 1 or orders.size == 0 or np.any(orders <= 1):
        raise ValueError("RDP orders must be a non-empty vector greater than one")


def gaussian_rdp(
    orders: np.ndarray,
    *,
    sensitivity: float,
    noise_std: float,
    steps: int = 1,
) -> np.ndarray:
    """Return the exact RDP curve for repeated Gaussian mechanisms."""
    orders = np.asarray(orders, dtype=np.float64)
    _validate_orders(orders)
    if sensitivity <= 0 or noise_std <= 0 or steps <= 0:
        raise ValueError("sensitivity, noise_std, and steps must be positive")
    return steps * orders * sensitivity**2 / (2.0 * noise_std**2)


def epsilon_from_rdp(
    orders: np.ndarray, rdp: np.ndarray, *, delta: float
) -> tuple[float, float]:
    """Convert an RDP curve with the standard safe RDP-to-DP bound."""
    orders = np.asarray(orders, dtype=np.float64)
    rdp = np.asarray(rdp, dtype=np.float64)
    _validate_orders(orders)
    if orders.shape != rdp.shape:
        raise ValueError("orders and rdp must have identical shapes")
    if not 0 < delta < 1:
        raise ValueError("delta must lie strictly between zero and one")
    eps = rdp + np.log(1.0 / delta) / (orders - 1.0)
    idx = int(np.argmin(eps))
    return float(eps[idx]), float(orders[idx])


def calibrate_gaussian(
    *,
    target_epsilon: float,
    delta: float,
    sensitivity: float = 1.0,
    steps: int = 1,
    orders: np.ndarray = DEFAULT_ORDERS,
    tolerance: float = 1e-10,
) -> GaussianCalibration:
    """Binary-search the smallest noise std meeting the target RDP bound."""
    if target_epsilon <= 0:
        raise ValueError("target_epsilon must be positive")
    orders = np.asarray(orders, dtype=np.float64)
    _validate_orders(orders)

    def evaluated(std: float) -> tuple[float, float, np.ndarray]:
        curve = gaussian_rdp(
            orders, sensitivity=sensitivity, noise_std=std, steps=steps
        )
        epsilon, order = epsilon_from_rdp(orders, curve, delta=delta)
        return epsilon, order, curve

    lo = np.finfo(np.float64).tiny
    hi = max(1.0, sensitivity)
    while evaluated(hi)[0] > target_epsilon:
        hi *= 2.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if evaluated(mid)[0] <= target_epsilon:
            hi = mid
        else:
            lo = mid
        if hi - lo <= tolerance * max(1.0, hi):
            break
    epsilon, order, curve = evaluated(hi)
    return GaussianCalibration(
        epsilon=epsilon,
        delta=delta,
        sensitivity=sensitivity,
        noise_std=hi,
        steps=steps,
        selected_order=order,
        orders=tuple(float(x) for x in orders),
        rdp=tuple(float(x) for x in curve),
    )
