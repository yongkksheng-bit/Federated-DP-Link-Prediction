import numpy as np
from scipy import sparse

from fed_dp_lp.p2_pilot import (
    candidate_arrays,
    evaluate_scores,
    metric_masks,
    sparse_cosine_scores,
)


def test_pilot_candidate_metrics_and_public_cosine():
    positive = np.asarray([[0, 1], [2, 3]])
    negative = np.asarray([[0, 2], [1, 4]])
    pairs, labels = candidate_arrays(positive, negative)
    homes = np.asarray([0, 0, 0, 1, 1])
    masks = metric_masks(pairs, homes)
    assert masks["intra"].tolist() == [True, False, True, False]
    features = sparse.csr_matrix(
        np.asarray(
            [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [0.0, 1.0]]
        )
    )
    scores = sparse_cosine_scores(features, pairs)
    metrics = evaluate_scores(labels, scores, masks)
    assert metrics["global"] == 1.0
    assert metrics["intra"] == 1.0
    assert metrics["cross"] == 1.0
