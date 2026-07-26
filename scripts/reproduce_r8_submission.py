"""Run the complete R7 artifact and R8 adversarial submission gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed: {command}\n"
            + "\n".join(completed.stdout.splitlines()[-80:])
        )
    return {
        "command": command,
        "returncode": completed.returncode,
        "output_tail": completed.stdout.splitlines()[-20:],
    }


def git_status() -> str:
    return subprocess.run(
        ["git", "status", "--short", "--untracked-files=no"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=ROOT / "tmp/r8_red_team/reproduction.json",
    )
    args = parser.parse_args()
    base_path = ROOT / "tmp/r8_red_team/r7_base_reproduction.json"
    base_path.parent.mkdir(parents=True, exist_ok=True)
    commands = [
        run(
            [
                sys.executable,
                "scripts/reproduce_r7_artifact.py",
                "--output",
                str(base_path),
            ]
        ),
        run([sys.executable, "scripts/audit_r8_red_team.py"]),
    ]
    base = json.loads(base_path.read_text(encoding="utf-8"))
    red_team_path = ROOT / "results/r8_red_team/audit.json"
    red_team = json.loads(red_team_path.read_text(encoding="utf-8"))
    tracked_changes = git_status()
    report = {
        "protocol": "R8_CLEAN_SUBMISSION_GATE_v1",
        "status": (
            "PASS"
            if base["status"] == "PASS"
            and red_team["status"] == "PASS"
            and not tracked_changes
            else "FAIL"
        ),
        "git_commit": base["git_commit"],
        "r7_base_status": base["status"],
        "r8_red_team_status": red_team["status"],
        "git_tracked_changes_after_build": tracked_changes,
        "sealed_holdout_accessed": False,
        "commands": commands,
        "artifacts": {
            **base["artifacts"],
            "r8_red_team": {
                "path": "results/r8_red_team/audit.json",
                "sha256": sha256(red_team_path),
            },
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit("R8 clean submission gate failed")


if __name__ == "__main__":
    main()
