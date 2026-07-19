"""Acquire only P2-allowlisted source bytes and emit a SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import urllib.request
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "source_registry.json"
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifests" / "p2_sources.json"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: pathlib.Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".partial")
    request = urllib.request.Request(url, headers={"User-Agent": "FedDPLP-P2/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        with temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
    temporary.replace(destination)


def iter_sources(dataset: dict) -> list[tuple[str, str, int | None]]:
    if "files" in dataset:
        return [
            (item["path"], item["source"], item.get("bytes"))
            for item in dataset["files"]
        ]
    suffix = ".zip" if dataset.get("expected_container") == "zip" else ".bin"
    return [(dataset["id"] + suffix, dataset["source"], None)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--acknowledge-local-research-only",
        action="store_true",
        help="Confirm that acquisition does not authorize redistribution.",
    )
    args = parser.parse_args()
    if not args.acknowledge_local_research_only:
        raise SystemExit("refusing acquisition without the rights-boundary acknowledgement")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    records: list[dict] = []
    for dataset in registry["datasets"]:
        for relative, url, expected_bytes in iter_sources(dataset):
            destination = RAW / dataset["id"] / pathlib.Path(relative).name
            if not destination.exists():
                download(url, destination)
            size = destination.stat().st_size
            if expected_bytes is not None and size != expected_bytes:
                raise RuntimeError(
                    f"byte-count mismatch for {dataset['id']}/{relative}: "
                    f"expected {expected_bytes}, observed {size}"
                )
            records.append(
                {
                    "dataset": dataset["id"],
                    "registry_path": relative,
                    "source": url,
                    "bytes": size,
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
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST} with {len(records)} source records")


if __name__ == "__main__":
    main()
