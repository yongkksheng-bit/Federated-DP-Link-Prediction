import numpy as np

from fed_dp_lp.phase_diagram import (
    leave_one_dataset_out_predictions,
    normalized_effective_rank,
    prediction_metrics,
    select_stratified_probe,
)


def test_stratified_probe_is_deterministic_balanced_and_disjoint():
    pairs = np.asarray(
        [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3], [2, 4], [3, 5]]
    )
    homes = np.asarray([0, 0, 1, 1, 0, 1])
    retained, probe = select_stratified_probe(
        pairs, homes, fraction=0.5, cap=4, seed=9
    )
    retained2, probe2 = select_stratified_probe(
        pairs, homes, fraction=0.5, cap=4, seed=9
    )
    assert np.array_equal(retained, retained2)
    assert np.array_equal(probe, probe2)
    assert not ({tuple(x) for x in retained} & {tuple(x) for x in probe})
    cross = homes[probe[:, 0]] != homes[probe[:, 1]]
    assert np.sum(cross) == np.sum(~cross) == 2


def test_effective_rank_and_lodo_predictions_are_finite():
    assert np.isclose(normalized_effective_rank(np.eye(3)), 1.0)
    datasets = np.asarray(["a", "a", "b", "b", "c", "c"])
    x = np.asarray([[0.0], [1.0], [0.2], [1.2], [0.4], [1.4]])
    y = 1.0 + 2.0 * x[:, 0]
    predictions = leave_one_dataset_out_predictions(
        datasets, x, y, ridge=1e-6
    )
    metrics = prediction_metrics(y, predictions)
    assert np.isfinite(predictions).all()
    assert metrics["mae"] < 1e-5
    assert metrics["sign_accuracy"] == 1.0
