import numpy as np

from fed_dp_lp.conservative_selector import (
    evaluate_policy,
    mean_t_interval,
    nested_lodo_safety_predictions,
)


def test_nested_lodo_predictions_have_nonnegative_fold_constant_margins():
    domains = np.repeat(np.array(["a", "b", "c", "d"]), 3)
    x = np.column_stack([np.tile(np.arange(3), 4), np.repeat(np.arange(4), 3)])
    y = 0.1 + 0.02 * x[:, 0] + 0.01 * x[:, 1]
    predictions, margins = nested_lodo_safety_predictions(
        domains, x, y, ridge=1.0
    )
    assert np.isfinite(predictions).all()
    assert np.all(margins >= 0)
    for domain in np.unique(domains):
        assert len(np.unique(margins[domains == domain])) == 1


def test_policy_metrics_penalize_harm_and_vacuous_abstention():
    domains = np.array(["a", "a", "b", "b"])
    gains = np.array([0.05, -0.01, 0.03, 0.0])
    metrics = evaluate_policy(
        domains, gains, np.array([True, True, True, False]), material_gain=0.02
    )
    assert metrics["negative_mean_gain_activations"] == 1
    assert np.isclose(metrics["material_precision"], 2 / 3)
    abstain = evaluate_policy(
        domains, gains, np.zeros(4, dtype=bool), material_gain=0.02
    )
    assert abstain["activation_fraction"] == 0.0
    assert abstain["positive_oracle_gain_capture"] == 0.0


def test_mean_t_interval_contains_sample_mean():
    values = np.array([0.01, 0.02, 0.03, 0.04])
    lower, upper = mean_t_interval(values)
    assert lower < values.mean() < upper
