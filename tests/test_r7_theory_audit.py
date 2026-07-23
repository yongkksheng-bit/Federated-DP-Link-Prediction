from __future__ import annotations

import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_r7", ROOT / "scripts/audit_r7_theory_contract.py"
)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_exhaustive_certificate_sensitivity_is_sqrt_two() -> None:
    valid, sensitivity = AUDIT.exhaustive_certificate_sensitivity()
    assert valid
    assert sensitivity == 2**0.5


def test_nested_summary_comparison_has_float_tolerance() -> None:
    assert not AUDIT.summaries_match(
        {"x": [1.0, {"y": 2}]}, {"x": [1.0 + 1e-13, {"y": 2}]}
    )
    assert AUDIT.summaries_match({"x": 1.0}, {"x": 1.01})


def test_reconstruct_summary_matches_frozen_result() -> None:
    config = AUDIT.json.loads(AUDIT.CONFIG.read_text(encoding="utf-8"))
    reported = AUDIT.json.loads(
        (AUDIT.RESULTS / "summary.json").read_text(encoding="utf-8")
    )
    records = AUDIT.read_jsonl(AUDIT.RESULTS / "records_strict.jsonl")
    rebuilt = AUDIT.reconstruct_summary(records, config, reported["provenance"])
    assert not AUDIT.summaries_match(rebuilt, reported)


def test_source_contract_is_machine_checkable() -> None:
    assert all(AUDIT.source_contract_checks(ROOT).values())
