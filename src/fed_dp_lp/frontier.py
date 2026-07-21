"""Operational privacy-utility frontier diagnostics for Gaussian graph releases."""

from __future__ import annotations

import numpy as np


def effective_noise_std(
    noise_std: float, *, clients: int, visibility: str
) -> float:
    if noise_std <= 0 or clients <= 0:
        raise ValueError("noise and client count must be positive")
    if visibility == "visible_messages":
        return float(noise_std * np.sqrt(clients))
    if visibility == "ideal_secagg":
        return float(noise_std)
    raise ValueError("unknown visibility model")


def expected_noise_energy(
    *, release_dimension: int, noise_std: float, clients: int, visibility: str
) -> float:
    if release_dimension <= 0:
        raise ValueError("release dimension must be positive")
    scale = effective_noise_std(
        noise_std, clients=clients, visibility=visibility
    )
    return float(release_dimension * scale**2)


def signal_noise_energy_ratio(
    signal: np.ndarray,
    *,
    noise_std: float,
    clients: int,
    visibility: str,
) -> float:
    values = np.asarray(signal, dtype=np.float64)
    if values.ndim != 2:
        raise ValueError("signal must be a matrix")
    noise = expected_noise_energy(
        release_dimension=values.size,
        noise_std=noise_std,
        clients=clients,
        visibility=visibility,
    )
    return float(np.linalg.norm(values) ** 2 / noise)


def degree_upper_energy_ratio(
    degrees: np.ndarray,
    *,
    encoding_dimension: int,
    noise_std: float,
    clients: int,
    visibility: str,
) -> float:
    """Upper bound the energy ratio for a row-bounded aggregation ``A Z``."""
    degrees = np.asarray(degrees, dtype=np.float64)
    if degrees.ndim != 1 or np.any(degrees < 0) or encoding_dimension <= 0:
        raise ValueError("invalid degrees or encoding dimension")
    noise = expected_noise_energy(
        release_dimension=len(degrees) * encoding_dimension,
        noise_std=noise_std,
        clients=clients,
        visibility=visibility,
    )
    return float(np.sum(degrees**2) / noise)


def gaussian_norm_interval(
    *,
    release_dimension: int,
    noise_std: float,
    clients: int,
    visibility: str,
    failure_probability: float,
) -> tuple[float, float]:
    """Laurent--Massart interval for the L2 norm of Gaussian release noise."""
    if not 0 < failure_probability < 1:
        raise ValueError("failure probability must lie in (0,1)")
    scale = effective_noise_std(
        noise_std, clients=clients, visibility=visibility
    )
    tail = np.log(2.0 / failure_probability)
    root_term = 2.0 * np.sqrt(release_dimension * tail)
    return (
        float(scale * np.sqrt(max(0.0, release_dimension - root_term))),
        float(
            scale
            * np.sqrt(release_dimension + root_term + 2.0 * tail)
        ),
    )
