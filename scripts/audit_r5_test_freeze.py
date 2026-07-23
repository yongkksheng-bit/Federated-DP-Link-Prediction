"""Final machine-checkable gate before the irreversible R5 test access."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/r5_graph_phase_confirmatory.json"
RUNNER = ROOT / "scripts/run_r5_graph_phase_test_once.py"
OUTPUT_AUDIT = ROOT / "results/r5_test_freeze_audit"
PREREG_AUDIT = ROOT / "results/r5_preregistration_audit/audit.json"
TEST_OUTPUT = ROOT / "results/r5_graph_phase_confirmatory"
SPLIT_MANIFEST = ROOT / "data/manifests/p3_split_manifest.json"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=ROOT, text=True
    ).strip()


def main() -> None:
    status = git("status", "--porcelain")
    tracked = set(git("ls-files").splitlines())
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    prereg = json.loads(PREREG_AUDIT.read_text(encoding="utf-8"))
    manifest = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))
    runner_text = RUNNER.read_text(encoding="utf-8")
    required_tracked = {
        "configs/r5_graph_phase_confirmatory.json",
        "docs/R5_CONFIRMATORY_PROTOCOL.md",
        "docs/R5_FINITE_POPULATION_THEOREM.md",
        "scripts/audit_r5_graph_phase.py",
        "scripts/audit_r5_preregistration.py",
        "scripts/audit_r5_test_freeze.py",
        "scripts/run_r5_graph_phase_test_once.py",
        "src/fed_dp_lp/r5_holdout.py",
        "tests/test_r5_holdout.py",
    }
    checks = {
        "clean_worktree": status == "",
        "all_r5_artifacts_tracked": required_tracked <= tracked,
        "preregistration_audit_pass": prereg["status"] == "PASS",
        "preregistration_config_hash_current": (
            prereg["hashes"]["r5_config_sha256"] == sha256(CONFIG)
        ),
        "sealed_test_untouched": (
            manifest["test_status"] == "encrypted_never_accessed"
            and manifest["test_access_count"] == 0
        ),
        "no_existing_r5_test_output": not TEST_OUTPUT.exists(),
        "runner_requires_clean_worktree": "require_clean_worktree()" in runner_text,
        "runner_has_one_time_output_guard": (
            "refusing a second test access" in runner_text
        ),
        "runner_requires_explicit_execute_flag": (
            "--execute-frozen-test-once" in runner_text
        ),
        "primary_cell_has_30_records": (
            config["confirmatory_primary_cell"]["records"] == 30
        ),
        "diagnostic_grid_not_primary": (
            "remaining privacy grid is diagnostic"
            in config["confirmatory_primary_cell"]["multiplicity"]
        ),
    }
    payload = {
        "protocol": config["protocol"],
        "runner_commit": git("rev-parse", "HEAD"),
        "hashes": {
            "config_sha256": sha256(CONFIG),
            "runner_sha256": sha256(RUNNER),
            "split_manifest_sha256": sha256(SPLIT_MANIFEST),
        },
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "test_accessed": False,
    }
    OUTPUT_AUDIT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_AUDIT / "audit.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload["status"] != "PASS":
        raise SystemExit("R5 test-freeze audit failed")


if __name__ == "__main__":
    main()
