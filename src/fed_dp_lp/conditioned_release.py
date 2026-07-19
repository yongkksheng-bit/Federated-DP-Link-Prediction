"""Public-score-conditioned edge-count releases with sensitivity one."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations_with_replacement

import numpy as np
from scipy import sparse
from sklearn.preprocessing import normalize


@dataclass(frozen=True)
class ConditionedLayout:
    cell_pairs: tuple[tuple[int, int], ...]
    bin_edges: tuple[float, ...]
    capacities: np.ndarray
    pair_to_index: dict[tuple[int, int], int]

    @property
    def bins(self) -> int:
        return len(self.bin_edges) - 1

    @property
    def dimension(self) -> int:
        return len(self.cell_pairs) * self.bins


def validate_bin_edges(bin_edges: np.ndarray) -> np.ndarray:
    edges = np.asarray(bin_edges, dtype=np.float64)
    if (
        edges.ndim != 1
        or edges.size < 3
        or not np.all(np.isfinite(edges))
        or np.any(np.diff(edges) <= 0)
        or edges[0] > 0.0
        or edges[-1] <= 1.0
    ):
        raise ValueError("bin edges must be increasing and cover cosine scores in [0,1]")
    return edges


def cosine_bin_indices(scores: np.ndarray, bin_edges: np.ndarray) -> np.ndarray:
    edges = validate_bin_edges(bin_edges)
    values = np.asarray(scores, dtype=np.float64)
    if np.any(~np.isfinite(values)):
        raise ValueError("public scores must be finite")
    values = np.clip(values, edges[0], np.nextafter(edges[-1], edges[0]))
    return np.searchsorted(edges[1:-1], values, side="right").astype(np.int64)


def canonical_pair_sample(
    nodes: int, *, maximum_pairs: int, seed: int
) -> np.ndarray:
    """Deterministically sample canonical node pairs from the public universe."""
    if nodes < 2 or maximum_pairs < 1:
        raise ValueError("nodes must exceed one and maximum_pairs must be positive")
    total = nodes * (nodes - 1) // 2
    size = min(total, maximum_pairs)
    if size == total:
        left, right = np.triu_indices(nodes, k=1)
        return np.column_stack((left, right)).astype(np.int64, copy=False)
    rng = np.random.default_rng(seed)
    indices = np.sort(rng.choice(total, size=size, replace=False, shuffle=False))
    # Invert NumPy/SciPy's row-major condensed upper-triangle indexing.
    left = (
        nodes
        - 2
        - np.floor(
            np.sqrt(-8.0 * indices + 4.0 * nodes * (nodes - 1) - 7.0) / 2.0
            - 0.5
        )
    ).astype(np.int64)
    right = (
        indices
        + left
        + 1
        - nodes * (nodes - 1) // 2
        + (nodes - left) * (nodes - left - 1) // 2
    ).astype(np.int64)
    return np.column_stack((left, right))


def _cosine_scores_normalized(
    normalized_features: sparse.csr_matrix, pairs: np.ndarray, *, chunk_size: int
) -> np.ndarray:
    result = np.empty(len(pairs), dtype=np.float64)
    for start in range(0, len(pairs), chunk_size):
        stop = min(start + chunk_size, len(pairs))
        part = pairs[start:stop]
        products = normalized_features[part[:, 0]].multiply(
            normalized_features[part[:, 1]]
        )
        result[start:stop] = np.asarray(products.sum(axis=1)).ravel()
    return np.clip(result, 0.0, 1.0)


def _cell_pair_lookup(layout: ConditionedLayout, cell_count: int) -> np.ndarray:
    lookup = np.empty((cell_count, cell_count), dtype=np.int64)
    for (left, right), index in layout.pair_to_index.items():
        lookup[left, right] = index
        lookup[right, left] = index
    return lookup


def public_capacity_layout(
    features: sparse.csr_matrix,
    cells: np.ndarray,
    bin_edges: np.ndarray,
    *,
    maximum_pairs: int,
    seed: int,
    dirichlet_alpha: float = 1.0,
    chunk_size: int = 100_000,
) -> ConditionedLayout:
    """Estimate positive public stratum capacities without reading private edges."""
    cells = np.asarray(cells, dtype=np.int64)
    edges = validate_bin_edges(bin_edges)
    if features.shape[0] != cells.size or np.any(cells < 0):
        raise ValueError("features and nonnegative public cells must share node count")
    labels = tuple(int(x) for x in np.unique(cells))
    if labels != tuple(range(len(labels))):
        raise ValueError("cell labels must be contiguous from zero")
    if dirichlet_alpha <= 0 or chunk_size < 1:
        raise ValueError("smoothing and chunk size must be positive")
    cell_pairs = tuple(combinations_with_replacement(labels, 2))
    pair_to_index = {pair: index for index, pair in enumerate(cell_pairs)}
    sample = canonical_pair_sample(
        cells.size, maximum_pairs=maximum_pairs, seed=seed
    )
    normalized = normalize(features, norm="l2", axis=1, copy=True).tocsr()
    scores = _cosine_scores_normalized(normalized, sample, chunk_size=chunk_size)
    bins = cosine_bin_indices(scores, edges)
    left = cells[sample[:, 0]]
    right = cells[sample[:, 1]]
    temporary = ConditionedLayout(
        cell_pairs=cell_pairs,
        bin_edges=tuple(float(value) for value in edges),
        capacities=np.empty(len(cell_pairs) * (len(edges) - 1)),
        pair_to_index=pair_to_index,
    )
    cell_indices = _cell_pair_lookup(temporary, len(labels))[left, right]
    dimension = len(cell_pairs) * (len(edges) - 1)
    sampled_counts = np.bincount(
        cell_indices * (len(edges) - 1) + bins, minlength=dimension
    ).astype(np.float64)
    total_pairs = float(cells.size * (cells.size - 1) // 2)
    capacities = (
        (sampled_counts + dirichlet_alpha)
        / (len(sample) + dirichlet_alpha * dimension)
        * total_pairs
    )
    return ConditionedLayout(
        cell_pairs=cell_pairs,
        bin_edges=tuple(float(value) for value in edges),
        capacities=capacities,
        pair_to_index=pair_to_index,
    )


def conditioned_counts(
    edges: np.ndarray,
    cells: np.ndarray,
    public_edge_scores: np.ndarray,
    layout: ConditionedLayout,
) -> np.ndarray:
    """Count each canonical private edge in exactly one public stratum."""
    edges = np.asarray(edges, dtype=np.int64)
    cells = np.asarray(cells, dtype=np.int64)
    scores = np.asarray(public_edge_scores, dtype=np.float64)
    if edges.size == 0:
        return np.zeros(layout.dimension, dtype=np.float64)
    if edges.ndim != 2 or edges.shape[1] != 2 or scores.shape != (len(edges),):
        raise ValueError("edges must have shape [m,2] and one score per edge")
    if np.any(edges < 0) or np.any(edges >= cells.size) or np.any(edges[:, 0] >= edges[:, 1]):
        raise ValueError("edges must be in-universe canonical pairs with u < v")
    bins = cosine_bin_indices(scores, np.asarray(layout.bin_edges))
    lookup = _cell_pair_lookup(layout, int(np.max(cells)) + 1)
    cell_indices = lookup[cells[edges[:, 0]], cells[edges[:, 1]]]
    return np.bincount(
        cell_indices * layout.bins + bins, minlength=layout.dimension
    ).astype(np.float64)


def release_conditioned_counts(
    local_counts: tuple[np.ndarray, ...],
    *,
    noise_std: float,
    visibility: str,
    rng: np.random.Generator,
) -> np.ndarray:
    if not local_counts or noise_std <= 0:
        raise ValueError("at least one local count vector and positive noise are required")
    local = np.stack(local_counts).astype(np.float64, copy=False)
    if visibility == "visible_messages":
        return np.sum(local + rng.normal(0.0, noise_std, size=local.shape), axis=0)
    if visibility == "ideal_secagg":
        return np.sum(local, axis=0) + rng.normal(0.0, noise_std, size=local.shape[1])
    raise ValueError("visibility must be visible_messages or ideal_secagg")


def conditioned_log_enrichment(
    noisy_counts: np.ndarray,
    layout: ConditionedLayout,
    *,
    alpha: float = 1.0,
    clip: float = 4.0,
) -> np.ndarray:
    """Return bounded cell-specific enrichment relative to each score bin."""
    counts = np.asarray(noisy_counts, dtype=np.float64)
    if counts.shape != (layout.dimension,) or alpha <= 0 or clip <= 0:
        raise ValueError("counts must match layout; alpha and clip must be positive")
    capacities = layout.capacities.reshape(-1, layout.bins)
    clipped = np.clip(counts.reshape(-1, layout.bins), 0.0, capacities)
    local_rate = (clipped + alpha) / (capacities + 2.0 * alpha)
    aggregate_count = np.sum(clipped, axis=0)
    aggregate_capacity = np.sum(capacities, axis=0)
    aggregate_rate = (aggregate_count + alpha) / (aggregate_capacity + 2.0 * alpha)
    enrichment = np.log(local_rate) - np.log(aggregate_rate[None, :])
    return np.clip(enrichment, -clip, clip).ravel() / clip


def score_conditioned_pairs(
    public_scores: np.ndarray,
    pairs: np.ndarray,
    cells: np.ndarray,
    residuals: np.ndarray,
    layout: ConditionedLayout,
    *,
    weight: float,
) -> np.ndarray:
    """Inference-closed score using public inputs and one DP release only."""
    public_scores = np.asarray(public_scores, dtype=np.float64)
    pairs = np.asarray(pairs, dtype=np.int64)
    residuals = np.asarray(residuals, dtype=np.float64)
    if weight <= 0 or public_scores.shape != (len(pairs),):
        raise ValueError("weight must be positive and scores must match pairs")
    if residuals.shape != (layout.dimension,):
        raise ValueError("residuals must match conditioned layout")
    bins = cosine_bin_indices(public_scores, np.asarray(layout.bin_edges))
    lookup = _cell_pair_lookup(layout, int(np.max(cells)) + 1)
    cell_indices = lookup[cells[pairs[:, 0]], cells[pairs[:, 1]]]
    indices = cell_indices * layout.bins + bins
    return public_scores + weight * residuals[indices]
