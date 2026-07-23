"""Archive immutable R5 access provenance and generated evidence hashes."""

from __future__ import annotations

import hashlib
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULT = ROOT / "results/r5_graph_phase_confirmatory"
MANIFEST = ROOT / "data/manifests/r5_test_access.json"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    access = json.loads((RESULT / "access.json").read_text(encoding="utf-8"))
    summary = json.loads((RESULT / "summary.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULT / "audit.json").read_text(encoding="utf-8"))
    if (
        access["test_access_count"] != 1
        or not summary["test_accessed"]
        or not audit["test_accessed"]
        or audit["status"] != "PASS"
    ):
        raise SystemExit("refusing to archive incomplete R5 evidence")
    payload = {
        "schema_version": 1,
        "protocol": access["protocol"],
        "status": "accessed_once_confirmatory_complete",
        "test_access_count": 1,
        "accessed_utc": access["accessed_utc"],
        "runner_commit": access["runner_commit"],
        "historical_p3_manifest_status": "encrypted_never_accessed at P3 creation; superseded for R5 by this access record",
        "decision": summary["decision"],
        "evidence": {
            name: {
                "path": f"results/r5_graph_phase_confirmatory/{name}",
                "sha256": sha256(RESULT / name),
                "bytes": (RESULT / name).stat().st_size,
            }
            for name in ("access.json", "records.jsonl", "summary.json", "audit.json")
        },
    }
    MANIFEST.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(MANIFEST)


if __name__ == "__main__":
    main()
