"""Acquire only source bytes allowlisted for the P2.1 confirmatory protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import urllib.request
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "p2_1_source_registry.json"
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifests" / "p2_1_sources.json"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledge-local-research-only", action="store_true")
    args = parser.parse_args()
    if not args.acknowledge_local_research_only:
        raise SystemExit("refusing acquisition without rights-boundary acknowledgement")
    if MANIFEST.exists():
        raise SystemExit("P2.1 source manifest already exists; refusing overwrite")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    records = []
    for dataset in registry["datasets"]:
        destination = RAW / dataset["id"] / f"{dataset['id']}.zip"
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(".zip.partial")
        request = urllib.request.Request(
            dataset["source"], headers={"User-Agent": "FedDPLP-P2.1/1"}
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            with partial.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        partial.replace(destination)
        records.append(
            {
                "dataset": dataset["id"],
                "source": dataset["source"],
                "bytes": destination.stat().st_size,
                "sha256": sha256(destination),
            }
        )
    payload = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "registry_sha256": sha256(REGISTRY),
        "rights_boundary": "local_scholarly_evaluation_no_redistribution",
        "files": records,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST}")


if __name__ == "__main__":
    main()
