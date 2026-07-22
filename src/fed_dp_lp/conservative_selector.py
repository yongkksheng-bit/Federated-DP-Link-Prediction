"""Domain-blocked conservative selection of a DP structural channel."""

from __future__ import annotations

import numpy as np
from scipy import stats

from .phase_diagram import ridge_fold_predict


def nested_lodo_safety_predictions(
    datasets: np.ndarray,
    features: np.ndarray,
    outcomes: np.ndarray,
    *,
    ridge: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return outer-LODO predictions and worst nested overprediction margins."""
    domains = np.asarray(datasets)
    values = np.asarray(features, dtype=np.float64)
    targets = np.asarray(outcomes, dtype=np.float64)
    predictions = np.empty(len(targets), dtype=np.float64)
    margins = np.empty(len(targets), dtype=np.float64)
    unique = np.unique(domains)
    if len(unique) < 4:
        raise ValueError("at least four domains are required for nested LODO")
    for held in unique:
        outer_test = domains == held
        outer_train = ~outer_test
        training_domains = np.unique(domains[outer_train])
        overpredictions: list[float] = []
        for calibration_domain in training_domains:
            calibration = outer_train & (domains == calibration_domain)
            fit = outer_train & ~calibration
            calibration_predictions = ridge_fold_predict(
                values[fit], targets[fit], values[calibration], ridge=ridge
            )
            overpredictions.extend(
                (calibration_predictions - targets[calibration]).tolist()
            )
        margin = max(0.0, max(overpredictions))
        predictions[outer_test] = ridge_fold_predict(
            values[outer_train], targets[outer_train], values[outer_test], ridge=ridge
        )
        margins[outer_test] = margin
    return predictions, margins


def mean_t_interval(values: np.ndarray, confidence: float = 0.95) -> tuple[float, float]:
    """Two-sided Student-t interval for independent domain-level means."""
    sample = np.asarray(values, dtype=np.float64)
    if sample.ndim != 1 or len(sample) < 2:
        raise ValueError("at least two one-dimensional observations are required")
    mean = float(sample.mean())
    sem = float(stats.sem(sample))
    if sem == 0.0:
        return mean, mean
    radius = float(stats.t.ppf((1.0 + confidence) / 2.0, len(sample) - 1) * sem)
    return mean - radius, mean + radius


def evaluate_policy(
    datasets: np.ndarray,
    gains: np.ndarray,
    activated: np.ndarray,
    *,
    material_gain: float,
) -> dict:
    """Evaluate nontriviality, no-harm, and oracle capture by dataset cell."""
    domains = np.asarray(datasets)
    outcomes = np.asarray(gains, dtype=np.float64)
    decisions = np.asarray(activated, dtype=bool)
    policy = np.where(decisions, outcomes, 0.0)
    unique = np.unique(domains)
    per_dataset = {
        str(domain): float(policy[domains == domain].mean()) for domain in unique
    }
    domain_means = np.asarray(list(per_dataset.values()))
    interval = mean_t_interval(domain_means)
    activated_count = int(decisions.sum())
    positive_oracle = np.maximum(outcomes, 0.0)
    oracle_total = float(positive_oracle.sum())
    return {
        "activation_count": activated_count,
        "activation_fraction": float(decisions.mean()),
        "activated_datasets": int(len(np.unique(domains[decisions]))) if activated_count else 0,
        "negative_mean_gain_activations": int(np.sum(decisions & (outcomes < 0.0))),
        "material_precision": float(np.mean(outcomes[decisions] >= material_gain))
        if activated_count else 0.0,
        "positive_oracle_gain_capture": float(policy.sum() / oracle_total)
        if oracle_total > 0 else 0.0,
        "macro_dataset_policy_gain": float(domain_means.mean()),
        "macro_dataset_policy_gain_95ci": [float(interval[0]), float(interval[1])],
        "worst_dataset_policy_gain": float(domain_means.min()),
        "per_dataset_policy_gain": per_dataset,
        "always_dp_macro_dataset_gain": float(np.mean([
            outcomes[domains == domain].mean() for domain in unique
        ])),
        "oracle_macro_dataset_gain": float(np.mean([
            positive_oracle[domains == domain].mean() for domain in unique
        ])),
    }
