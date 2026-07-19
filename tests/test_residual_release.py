import numpy as np

from fed_dp_lp.block_release import make_block_layout
from fed_dp_lp.residual_release import residual_map, score_with_residual


def test_residual_maps_are_bounded_and_scores_preserve_public_component():
    groups = np.asarray([0, 0, 1, 1, 2, 2])
    layout = make_block_layout(groups)
    counts = np.arange(1, layout.dimension + 1, dtype=float)
    pairs = np.asarray([[0, 1], [0, 2], [2, 4]])
    public = np.asarray([0.2, 0.4, 0.6])
    for transform in ("centered_block_rank", "clipped_log_density_zscore"):
        residual = residual_map(counts, layout, transform=transform)
        assert np.max(np.abs(residual)) <= 1.0
        scores = score_with_residual(
            public, pairs, groups, residual, layout, weight=0.01
        )
        assert np.max(np.abs(scores - public)) <= 0.01 + 1e-12
