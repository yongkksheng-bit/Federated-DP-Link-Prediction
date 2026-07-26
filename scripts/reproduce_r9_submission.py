"""Run the R9 submission-preparation gate from a clean checkout."""

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


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
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
        default=ROOT / "tmp/r9_submission/reproduction.json",
    )
    args = parser.parse_args()

    r8_path = ROOT / "tmp/r9_submission/r8_base_reproduction.json"
    r8_path.parent.mkdir(parents=True, exist_ok=True)
    commands = [
        run(
            [
                sys.executable,
                "scripts/reproduce_r8_submission.py",
                "--output",
                str(r8_path),
            ]
        )
    ]
    r8 = json.loads(r8_path.read_text(encoding="utf-8"))
    built_pdf = ROOT / "manuscript/main.pdf"
    tracked_pdf = ROOT / "output/pdf/certfed_lp_r9_submission_ready.pdf"
    if not built_pdf.exists() or not tracked_pdf.exists():
        raise FileNotFoundError("built and tracked R9 manuscript PDFs are required")

    built_hash = sha256(built_pdf)
    tracked_hash = sha256(tracked_pdf)
    tracked_changes = git("status", "--short", "--untracked-files=no")
    report = {
        "protocol": "R9_CLEAN_SUBMISSION_PREPARATION_v1",
        "status": (
            "PASS"
            if r8["status"] == "PASS"
            and built_hash == tracked_hash
            and not tracked_changes
            else "FAIL"
        ),
        "git_commit": git("rev-parse", "HEAD"),
        "r8_base_status": r8["status"],
        "git_tracked_changes_after_build": tracked_changes,
        "sealed_holdout_accessed": False,
        "commands": commands,
        "artifacts": {
            "built_manuscript": {
                "path": "manuscript/main.pdf",
                "sha256": built_hash,
            },
            "tracked_r9_manuscript": {
                "path": "output/pdf/certfed_lp_r9_submission_ready.pdf",
                "sha256": tracked_hash,
            },
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit("R9 clean submission-preparation gate failed")


if __name__ == "__main__":
    main()
