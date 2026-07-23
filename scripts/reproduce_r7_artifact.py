"""Reproduce the tracked R7 audit, figures, tests, and manuscript build."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
from importlib import metadata


ROOT = pathlib.Path(__file__).resolve().parents[1]


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], *, cwd: pathlib.Path = ROOT) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env={**os.environ, "PYTHONHASHSEED": "0"},
    )
    if completed.returncode:
        tail = "\n".join(completed.stdout.splitlines()[-80:])
        raise RuntimeError(f"command failed ({completed.returncode}): {command}\n{tail}")
    return {
        "command": command,
        "returncode": completed.returncode,
        "output_tail": completed.stdout.splitlines()[-20:],
    }


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return completed.stdout.strip()


def package_versions() -> dict[str, str]:
    packages = [
        "cryptography",
        "matplotlib",
        "networkx",
        "numpy",
        "pytest",
        "scikit-learn",
        "scipy",
    ]
    versions = {}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "NOT_INSTALLED"
    return versions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=ROOT / "tmp/r7_independent_audit/reproduction.json",
    )
    args = parser.parse_args()

    strict_records = ROOT / "results/r5_graph_phase_confirmatory/records_strict.jsonl"
    if not strict_records.exists():
        raise FileNotFoundError(
            "tracked strict R5 record export is required for clean reproduction"
        )
    commands = []
    commands.append(run([sys.executable, "-m", "pytest", "-q"]))
    commands.append(run([sys.executable, "scripts/audit_r7_theory_contract.py"]))
    commands.append(run([sys.executable, "scripts/build_r6_figures.py"]))
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        raise RuntimeError("latexmk is required to reproduce the manuscript PDF")
    commands.append(
        run(
            [
                latexmk,
                "-pdf",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "main.tex",
            ],
            cwd=ROOT / "manuscript",
        )
    )
    manuscript_pdf = ROOT / "manuscript/main.pdf"
    if not manuscript_pdf.exists():
        raise RuntimeError("manuscript build did not produce manuscript/main.pdf")

    tracked_changes = git("status", "--short", "--untracked-files=no")
    report = {
        "protocol": "R7_CLEAN_ARTIFACT_REPRODUCTION_v1",
        "status": "PASS" if not tracked_changes else "FAIL",
        "git_commit": git("rev-parse", "HEAD"),
        "git_branch": git("branch", "--show-current"),
        "git_tracked_changes_after_build": tracked_changes,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "executable": sys.executable,
            "packages": package_versions(),
            "latexmk": latexmk,
        },
        "commands": commands,
        "artifacts": {
            "strict_records": {
                "path": str(strict_records.relative_to(ROOT)),
                "sha256": sha256(strict_records),
                "bytes": strict_records.stat().st_size,
            },
            "summary": {
                "path": "results/r5_graph_phase_confirmatory/summary.json",
                "sha256": sha256(
                    ROOT / "results/r5_graph_phase_confirmatory/summary.json"
                ),
            },
            "theory_audit": {
                "path": "results/r7_independent_audit/theory_contract.json",
                "sha256": sha256(
                    ROOT / "results/r7_independent_audit/theory_contract.json"
                ),
            },
            "manuscript_pdf": {
                "path": "manuscript/main.pdf",
                "sha256": sha256(manuscript_pdf),
                "bytes": manuscript_pdf.stat().st_size,
            },
        },
        "sealed_test_reaccessed": False,
        "note": (
            "This reconstructs derived artifacts from tracked evidence. It "
            "does not decrypt, regenerate, or query the sealed R5 holdout."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit("tracked artifacts changed during clean reproduction")


if __name__ == "__main__":
    main()
