"""Edge-DP reciprocal affinity profiles for inference-closed link prediction."""

from __future__ import annotations

import numpy as np
from scipy import sparse

from .gap_adaptation import normalize_rows, score_pairs_from_channels


RAP_L2_SENSITIVITY = np.sqrt(2.0)


def reciprocal_profile_counts(
    edges: np.ndarray, cells: np.ndarray, *, node_count: int
) -> np.ndarray:
    """Count neighbor public cells for every node.

    A canonical edge ``{u,v}`` increments ``(u, cell(v))`` and
    ``(v, cell(u))`` exactly once.
    """
    edges = np.asarray(edges, dtype=np.int64)
    cells = np.asarray(cells, dtype=np.int64)
    if cells.shape != (node_count,) or np.any(cells < 0):
        raise ValueError("cells must be one nonnegative label per node")
    if edges.size == 0:
        return np.zeros((node_count, int(np.max(cells)) + 1), dtype=np.float64)
    if edges.ndim != 2 or edges.shape[1] != 2:
        raise ValueError("edges must have shape [m,2]")
    if np.any(edges < 0) or np.any(edges >= node_count) or np.any(edges[:, 0] >= edges[:, 1]):
        raise ValueError("edges must be canonical in-universe pairs")
    output = np.zeros((node_count, int(np.max(cells)) + 1), dtype=np.float64)
    np.add.at(output, (edges[:, 0], cells[edges[:, 1]]), 1.0)
    np.add.at(output, (edges[:, 1], cells[edges[:, 0]]), 1.0)
    return output


def joint_profile_scales(profile_energy_fraction: float) -> tuple[float, float]:
    gamma = float(profile_energy_fraction)
    if not 0 < gamma < 1:
        raise ValueError("profile energy fraction must lie in (0,1)")
    return np.sqrt(1.0 - gamma), np.sqrt(gamma)


def release_joint_semantic_profile(
    adjacency: sparse.csr_matrix,
    encoded: np.ndarray,
    local_profiles: tuple[np.ndarray, ...],
    *,
    profile_energy_fraction: float,
    noise_std: float,
    visibility: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Release semantic aggregation and node-cell profiles in one query."""
    if not local_profiles or noise_std <= 0:
        raise ValueError("local profiles and positive noise are required")
    encoded = normalize_rows(encoded)
    if adjacency.shape != (len(encoded), len(encoded)):
        raise ValueError("adjacency and encoded node count must match")
    shapes = {np.asarray(profile).shape for profile in local_profiles}
    if len(shapes) != 1 or next(iter(shapes))[0] != len(encoded):
        raise ValueError("local profiles must share node dimension")
    semantic_scale, profile_scale = joint_profile_scales(profile_energy_fraction)
    semantic_signal = semantic_scale * (adjacency @ encoded)
    profile_signal = profile_scale * np.sum(np.stack(local_profiles), axis=0)
    if visibility == "visible_messages":
        effective_noise = noise_std * np.sqrt(len(local_profiles))
    elif visibility == "ideal_secagg":
        effective_noise = noise_std
    else:
        raise ValueError("unknown visibility model")
    semantic = semantic_signal + rng.normal(
        0.0, effective_noise, size=semantic_signal.shape
    )
    profile = profile_signal + rng.normal(
        0.0, effective_noise, size=profile_signal.shape
    )
    return semantic / semantic_scale, profile / profile_scale


def reciprocal_profile_scores(
    noisy_profiles: np.ndarray,
    pairs: np.ndarray,
    cells: np.ndarray,
    *,
    prior_strength: float,
    effective_noise_std: float,
    log_lift_clip: float = 4.0,
) -> np.ndarray:
    """Score mutual endpoint-to-cell affinity with public-prior shrinkage."""
    profiles = np.asarray(noisy_profiles, dtype=np.float64)
    pairs = np.asarray(pairs, dtype=np.int64)
    cells = np.asarray(cells, dtype=np.int64)
    if profiles.ndim != 2 or profiles.shape[0] != len(cells):
        raise ValueError("profiles and cells must share node count")
    if pairs.ndim != 2 or pairs.shape[1] != 2:
        raise ValueError("pairs must have shape [m,2]")
    if prior_strength <= 0 or effective_noise_std < 0 or log_lift_clip <= 0:
        raise ValueError("invalid shrinkage or noise parameters")
    cell_count = profiles.shape[1]
    if np.any(cells < 0) or np.any(cells >= cell_count):
        raise ValueError("cell labels exceed profile columns")
    public_prior = np.bincount(cells, minlength=cell_count).astype(np.float64)
    public_prior /= np.sum(public_prior)
    clipped = np.maximum(profiles, 0.0)
    totals = np.sum(clipped, axis=1, keepdims=True)
    posterior = (
        clipped + prior_strength * public_prior[None, :]
    ) / (totals + prior_strength)
    floor = 1e-12
    lift = np.log(np.maximum(posterior, floor)) - np.log(
        np.maximum(public_prior[None, :], floor)
    )
    lift = np.clip(lift, -log_lift_clip, log_lift_clip) / log_lift_clip
    noise_floor = effective_noise_std * np.sqrt(cell_count)
    reliability = np.divide(
        totals[:, 0],
        totals[:, 0] + prior_strength + noise_floor,
        out=np.zeros(len(totals), dtype=np.float64),
        where=(totals[:, 0] + prior_strength + noise_floor) > 0,
    )
    left = reliability[pairs[:, 0]] * lift[pairs[:, 0], cells[pairs[:, 1]]]
    right = reliability[pairs[:, 1]] * lift[pairs[:, 1], cells[pairs[:, 0]]]
    return 0.5 * (left + right)


def score_rap_pairs(
    semantic_channels: tuple[np.ndarray, ...],
    noisy_profiles: np.ndarray,
    pairs: np.ndarray,
    cells: np.ndarray,
    *,
    profile_weight: float,
    prior_strength: float,
    effective_profile_noise_std: float,
) -> np.ndarray:
    if profile_weight <= 0:
        raise ValueError("profile weight must be positive")
    semantic = score_pairs_from_channels(semantic_channels, pairs)
    reciprocal = reciprocal_profile_scores(
        noisy_profiles,
        pairs,
        cells,
        prior_strength=prior_strength,
        effective_noise_std=effective_profile_noise_std,
    )
    return semantic + profile_weight * reciprocal
