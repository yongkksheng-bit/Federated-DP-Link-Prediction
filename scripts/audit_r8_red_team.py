"""Adversarial R8 checks for theorem assumptions and forbidden upgrades."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import pathlib
from typing import Any

import numpy as np

from fed_dp_lp.private_certificate import certificate_lower_bound
from fed_dp_lp.r5_holdout import certification_mask


ROOT = pathlib.Path(__file__).resolve().parents[1]


def conditional_bernoulli_probabilities(
    population_size: int, probability: float, sample_size: int
) -> np.ndarray:
    """Enumerate P(C=A | |C|=sample_size) for all fixed-size subsets."""
    if not 0 < probability < 1:
        raise ValueError("probability must lie in (0,1)")
    if not 0 <= sample_size <= population_size:
        raise ValueError("invalid sample size")
    subsets = list(itertools.combinations(range(population_size), sample_size))
    mass = probability**sample_size * (1 - probability) ** (
        population_size - sample_size
    )
    weights = np.full(len(subsets), mass, dtype=np.float64)
    return weights / weights.sum()


def adaptive_public_hash_counterexample() -> dict[str, float | int | bool]:
    """Select a target population after observing a public hash assignment."""
    nodes = 80
    universe = np.asarray(
        [(left, right) for left in range(nodes) for right in range(left + 1, nodes)],
        dtype=np.int64,
    )
    assigned = certification_mask(
        universe,
        nodes=nodes,
        dataset="R8-public-hash-attack",
        seed=0,
        salt="PUBLIC-R8-SALT",
        probability=1.0 / 3.0,
    )
    adaptive_population = universe[assigned][:200]
    realized = certification_mask(
        adaptive_population,
        nodes=nodes,
        dataset="R8-public-hash-attack",
        seed=0,
        salt="PUBLIC-R8-SALT",
        probability=1.0 / 3.0,
    )
    rate = float(np.mean(realized))
    return {
        "population_size": len(adaptive_population),
        "realized_certification_rate": rate,
        "all_selected_for_certification": bool(np.all(realized)),
        "violates_preassignment_population_freeze": rate == 1.0,
    }


def unstable_partition_counterexample() -> dict[str, int | bool]:
    """Show index-based role assignment can change many records after one add."""
    original = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
    adjacent = [(0, 1), *original]

    def training_role(edges: list[tuple[int, int]]) -> set[tuple[int, int]]:
        return {edge for index, edge in enumerate(sorted(edges)) if index % 2 == 0}

    before = training_role(original)
    after = training_role(adjacent)
    changed_existing = len((before ^ after) & set(original))
    return {
        "raw_edge_additions": 1,
        "existing_role_changes": changed_existing,
        "one_raw_change_reassigns_many_existing_edges": changed_existing > 1,
    }


def certificate_algebra_attack(*, trials: int = 5000) -> dict[str, float | bool]:
    """Search adversarial good-event values for a lower-bound violation."""
    rng = np.random.default_rng(80260726)
    maximum_violation = -math.inf
    checked = 0
    for _ in range(trials):
        count = int(rng.integers(80, 20000))
        mean = float(rng.uniform(-1.0, 1.0))
        true_sum = count * mean
        coordinate_std = float(rng.uniform(0.1, 20.0))
        beta_sum, beta_count, beta_sampling = 0.01, 0.01, 0.03
        from scipy.stats import norm

        sum_bound = coordinate_std * norm.ppf(1 - beta_sum / 2)
        count_bound = coordinate_std * norm.ppf(1 - beta_count / 2)
        noisy_sum = true_sum + rng.uniform(-sum_bound, sum_bound)
        noisy_count = count + rng.uniform(-count_bound, count_bound)
        result = certificate_lower_bound(
            np.asarray([noisy_sum]),
            np.asarray([noisy_count]),
            coordinate_noise_std=coordinate_std,
            beta_sum=beta_sum,
            beta_count=beta_count,
            beta_sampling=beta_sampling,
            dependence_factor=1.0,
            minimum_count_lower=50.0,
        )
        if result.valid[0]:
            sampling = math.sqrt(2 * math.log(1 / beta_sampling) / count)
            valid_target_lower = mean - sampling
            maximum_violation = max(
                maximum_violation,
                float(result.lower_bound[0] - valid_target_lower),
            )
            checked += 1
    return {
        "valid_good_event_trials": checked,
        "maximum_lower_bound_violation": maximum_violation,
        "no_violation": maximum_violation <= 1e-12,
    }


def approximate_dp_d_star(epsilon: float, delta: float, eta: float) -> float:
    """Solve the exact approximate-DP Le Cam condition used in the appendix."""
    if epsilon <= 0 or not 0 <= delta < 1 or not 0 < eta < 0.45:
        raise ValueError("invalid lower-bound parameters")
    epsilon_r = 2 * epsilon
    delta_r = (1 + math.exp(epsilon)) * delta

    def constraint(distance: float) -> float:
        return (
            0.9 * math.exp(-10 * epsilon_r * distance)
            - 10 * distance * delta_r
            - 2 * eta
        )

    lower, upper = 0.0, 1.0
    while constraint(upper) > 0:
        upper *= 2
    for _ in range(200):
        midpoint = (lower + upper) / 2
        if constraint(midpoint) > 0:
            lower = midpoint
        else:
            upper = midpoint
    return upper


def lower_bound_scope_check() -> dict[str, float | bool]:
    epsilon, eta = 1.0, 0.1
    pure = approximate_dp_d_star(epsilon, 0.0, eta)
    expected_pure = math.log(0.9 / (2 * eta)) / (20 * epsilon)
    loose_delta = approximate_dp_d_star(epsilon, 0.4, eta)
    return {
        "pure_d_star": pure,
        "pure_closed_form": expected_pure,
        "pure_formula_matches": bool(
            np.isclose(pure, expected_pure, rtol=0, atol=1e-12)
        ),
        "large_delta_d_star": loose_delta,
        "large_delta_weakens_privacy_term": loose_delta < 0.5 * pure,
        "generic_approximate_dp_inverse_epsilon_claim_is_unsafe": True,
    }


def manuscript_contract_checks() -> dict[str, bool]:
    sections = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "manuscript/sections").glob("*.tex"))
    )
    normalized = " ".join(sections.split())
    return {
        "population_precedes_assignment_outputs": (
            "fixed independently of the assignment outputs" in normalized
        ),
        "random_oracle_and_prf_are_alternatives": (
            "random-oracle model" in normalized
            and "secret-key PRF" in normalized
            and "alternative computational or ideal contracts" in normalized
        ),
        "prf_advantage_is_accounted": (
            "adds the distinguishing advantage" in normalized
        ),
        "raw_graph_upgrade_forbidden": (
            "not silently upgraded to raw pre-partition" in normalized
        ),
        "pairwise_not_auc": (
            "do not claim that the registered pairwise certificate is an AUC"
            in normalized
        ),
        "approximate_dp_lower_bound_is_conditional": (
            "when $D_\\star>0$" in normalized
        ),
        "pure_dp_inverse_epsilon_scope": (
            "For pure DP" in normalized and "1/(\\eps\\alpha)" in normalized
        ),
        "external_review_not_claimed": (
            "not an external peer review" in normalized.lower()
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=ROOT / "results/r8_red_team/audit.json",
    )
    args = parser.parse_args()

    probabilities = conditional_bernoulli_probabilities(8, 1 / 3, 3)
    hash_attack = adaptive_public_hash_counterexample()
    split_attack = unstable_partition_counterexample()
    algebra = certificate_algebra_attack()
    lower_scope = lower_bound_scope_check()
    manuscript = manuscript_contract_checks()
    checks = {
        "conditional_fixed_size_assignment_is_uniform": bool(
            np.allclose(
                probabilities,
                np.full_like(probabilities, 1 / len(probabilities)),
                rtol=0,
                atol=1e-15,
            )
        ),
        "adaptive_public_hash_attack_succeeds": bool(
            hash_attack["violates_preassignment_population_freeze"]
        ),
        "unstable_raw_partition_attack_succeeds": bool(
            split_attack["one_raw_change_reassigns_many_existing_edges"]
        ),
        "certificate_good_event_algebra_survives_attack": bool(
            algebra["no_violation"]
        ),
        "pure_dp_lower_bound_formula_reproduces": bool(
            lower_scope["pure_formula_matches"]
        ),
        "approximate_dp_scope_requires_exact_d_star": bool(
            lower_scope["large_delta_weakens_privacy_term"]
        ),
        **manuscript,
    }
    report: dict[str, Any] = {
        "protocol": "R8_PRE_SUBMISSION_RED_TEAM_v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "attacks": {
            "adaptive_public_hash": hash_attack,
            "unstable_partition": split_attack,
            "certificate_algebra": algebra,
            "lower_bound_scope": lower_scope,
        },
        "interpretation": (
            "A passing attack means the counterexample was successfully "
            "exhibited and the manuscript explicitly excludes that invalid "
            "upgrade; it does not mean the invalid protocol is safe."
        ),
        "sealed_holdout_accessed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit("R8 red-team audit failed")


if __name__ == "__main__":
    main()
