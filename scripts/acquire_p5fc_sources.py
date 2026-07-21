"""Acquire only the frozen P5FC adjacency and public-feature artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import urllib.request
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/p5fc_source_registry.json"
RAW = ROOT / "data/raw/p5fc"
MANIFEST = ROOT / "data/manifests/p5fc_sources.json"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_google_file(file_id: str, destination: pathlib.Path) -> None:
    url = f"https://drive.usercontent.google.com/download?id={file_id}&confirm=t"
    request = urllib.request.Request(url, headers={"User-Agent": "FedDPLP-P5FC/1"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".partial")
    curl = shutil.which("curl")
    if curl is not None:
        print(f"downloading {destination.name} with resumable curl", flush=True)
        subprocess.run(
            [
                curl,
                "--location",
                "--fail",
                "--retry",
                "5",
                "--retry-all-errors",
                "--continue-at",
                "-",
                "--output",
                str(temporary),
                url,
            ],
            check=True,
        )
        temporary.replace(destination)
        return
    with urllib.request.urlopen(request, timeout=300) as response:
        with temporary.open("wb") as output:
            while chunk := response.read(8 * 1024 * 1024):
                output.write(chunk)
    temporary.replace(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledge-local-research-only", action="store_true")
    args = parser.parse_args()
    if not args.acknowledge_local_research_only:
        raise SystemExit("rights-boundary acknowledgement is required")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    prohibited = {
        item for dataset in registry["datasets"]
        for item in dataset["prohibited_google_drive_ids"]
    }
    allowlisted = {
        item["google_drive_id"] for dataset in registry["datasets"]
        for item in dataset["files"]
    }
    if prohibited & allowlisted:
        raise RuntimeError("a prohibited label/role artifact is allowlisted")

    records = []
    for dataset in registry["datasets"]:
        for item in dataset["files"]:
            destination = RAW / dataset["id"] / item["path"]
            if not destination.exists():
                download_google_file(item["google_drive_id"], destination)
            records.append({
                "dataset": dataset["id"],
                "path": item["path"],
                "role": item["role"],
                "google_drive_id": item["google_drive_id"],
                "bytes": destination.stat().st_size,
                "sha256": sha256(destination),
            })

    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "registry_sha256": sha256(REGISTRY),
        "rights_boundary": registry["rights_boundary"],
        "labels_or_source_roles_acquired": False,
        "files": records,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST} with {len(records)} allowlisted files")


if __name__ == "__main__":
    main()
