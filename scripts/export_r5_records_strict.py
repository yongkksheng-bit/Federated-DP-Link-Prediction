"""Export a strict-JSON R5 record copy while preserving immutable raw output."""

from __future__ import annotations

import hashlib
import json
import math
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results/r5_graph_phase_confirmatory"
RAW_RECORDS = OUTPUT / "records.jsonl"
STRICT_RECORDS = OUTPUT / "records_strict.jsonl"
AUDIT = OUTPUT / "serialization_audit.json"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if STRICT_RECORDS.exists() or AUDIT.exists():
        raise SystemExit("strict R5 export already exists; refusing overwrite")
    rows = [
        json.loads(line)
        for line in RAW_RECORDS.read_text(encoding="utf-8").splitlines()
        if line
    ]
    replacements = 0
    with STRICT_RECORDS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            lower = row["certificate_lower_bound"]
            if isinstance(lower, float) and not math.isfinite(lower):
                if row["certificate_valid"]:
                    raise RuntimeError(
                        "valid certificate has a non-finite lower bound"
                    )
                row["certificate_lower_bound"] = None
                replacements += 1
            handle.write(
                json.dumps(row, sort_keys=True, allow_nan=False) + "\n"
            )
    reparsed = [
        json.loads(
            line,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant: {value}")
            ),
        )
        for line in STRICT_RECORDS.read_text(encoding="utf-8").splitlines()
        if line
    ]
    checks = {
        "raw_output_preserved": RAW_RECORDS.exists(),
        "record_count_preserved": len(reparsed) == len(rows) == 1500,
        "only_invalid_bounds_are_null": all(
            (row["certificate_lower_bound"] is None)
            == (not row["certificate_valid"])
            for row in reparsed
        ),
        "strict_json_reparse": True,
    }
    payload = {
        "operation": "non_destructive_strict_json_export",
        "test_reaccessed": False,
        "raw_path": str(RAW_RECORDS.relative_to(ROOT)),
        "raw_sha256": sha256(RAW_RECORDS),
        "strict_path": str(STRICT_RECORDS.relative_to(ROOT)),
        "strict_sha256": sha256(STRICT_RECORDS),
        "nonfinite_bounds_replaced_with_null": replacements,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    AUDIT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload["status"] != "PASS":
        raise SystemExit("R5 strict-JSON export failed")


if __name__ == "__main__":
    main()
