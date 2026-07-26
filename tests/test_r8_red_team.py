from __future__ import annotations

import importlib.util
import pathlib

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_r8", ROOT / "scripts/audit_r8_red_team.py"
)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_conditional_bernoulli_is_uniform() -> None:
    probabilities = AUDIT.conditional_bernoulli_probabilities(7, 0.2, 3)
    assert len(probabilities) == 35
    assert np.allclose(probabilities, np.full(35, 1 / 35))


def test_adaptive_public_hash_attack_is_detected() -> None:
    result = AUDIT.adaptive_public_hash_counterexample()
    assert result["all_selected_for_certification"]
    assert result["realized_certification_rate"] == 1.0


def test_unstable_partition_changes_existing_roles() -> None:
    result = AUDIT.unstable_partition_counterexample()
    assert result["raw_edge_additions"] == 1
    assert result["existing_role_changes"] > 1


def test_certificate_good_event_algebra() -> None:
    result = AUDIT.certificate_algebra_attack(trials=1000)
    assert result["valid_good_event_trials"] > 0
    assert result["no_violation"]


def test_pure_dp_lower_bound_solution() -> None:
    result = AUDIT.lower_bound_scope_check()
    assert result["pure_formula_matches"]
    assert result["large_delta_weakens_privacy_term"]
