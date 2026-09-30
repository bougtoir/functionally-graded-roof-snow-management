from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "topic",
    "source_type",
    "title",
    "url",
    "identifier",
    "retrieved_at_utc",
    "acquisition_conditions",
    "storage_path",
    "file_size_bytes",
    "sha256",
    "usage_conditions",
    "completeness",
    "local_status",
]


def first(record: dict[str, object], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None:
            return str(value)
    return ""


def file_status(storage_path: str, expected_size: str, expected_sha: str) -> str:
    if not storage_path:
        return "no_path"
    candidate = Path(storage_path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    if not candidate.exists():
        return "not_recovered"
    content = candidate.read_bytes()
    if expected_size and len(content) != int(expected_size):
        return "size_mismatch"
    if expected_sha and hashlib.sha256(content).hexdigest() != expected_sha:
        return "checksum_mismatch"
    return "verified"


def normalize(
    record: dict[str, object],
    *,
    topic: str,
    source_type: str = "",
) -> dict[str, str]:
    storage_path = first(record, "storage_path", "saved_path", "file")
    size = first(record, "file_size_bytes", "bytes")
    digest = first(record, "sha256")
    method = first(record, "method", "request_method")
    condition = first(
        record,
        "acquisition_conditions",
        "condition",
        "retrieval",
    )
    if method:
        condition = f"{method}; {condition}".strip("; ")
    return {
        "topic": topic,
        "source_type": source_type or first(record, "source_type", "category"),
        "title": first(record, "title"),
        "url": first(record, "source_url", "url"),
        "identifier": first(record, "identifier", "source_id"),
        "retrieved_at_utc": first(
            record,
            "retrieved_at_utc",
            "retrieved_utc",
        ),
        "acquisition_conditions": condition,
        "storage_path": storage_path,
        "file_size_bytes": size,
        "sha256": digest,
        "usage_conditions": first(
            record,
            "usage_conditions",
            "use_terms",
        ),
        "completeness": first(record, "completeness"),
        "local_status": file_status(storage_path, size, digest),
    }


def load_records(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    if isinstance(payload, list):
        for record in payload:
            rows.append(
                normalize(
                    cast(dict[str, object], record),
                    topic=path.stem,
                )
            )
        return rows

    topic = str(payload.get("topic", path.stem))
    for key in ("records", "artifacts", "derivatives"):
        for record in payload.get(key, []):
            rows.append(
                normalize(
                    cast(dict[str, object], record),
                    topic=topic,
                    source_type=key.rstrip("s"),
                )
            )
    return rows


def main() -> None:
    paths = sorted((ROOT / "data" / "metadata").glob("research_sources_*.json"))
    paths.extend(sorted((ROOT / "data" / "metadata").glob("jma_*.json")))
    paths.extend(
        sorted((ROOT / "data" / "raw" / "research_snapshots").rglob("*.json"))
    )
    rows = [row for path in paths for row in load_records(path)]
    destination = ROOT / "data" / "metadata" / "acquisition_ledger.csv"
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    statuses: dict[str, int] = {}
    for row in rows:
        status = row["local_status"]
        statuses[status] = statuses.get(status, 0) + 1
    print(json.dumps({"records": len(rows), "local_status": statuses}))


if __name__ == "__main__":
    main()
