from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = (
    "graded-roof-snow-research/0.1 "
    "(https://github.com/bougtoir/functionally-graded-roof-snow-management)"
)


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_").lower()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(url: str) -> tuple[bytes, requests.Response]:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        timeout=90,
    )
    response.raise_for_status()
    return response.content, response


def literature_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    path = ROOT / "references" / "literature_database.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            doi = row["doi_or_identifier"]
            if not doi.startswith("10."):
                continue
            records.append(
                {
                    "source_id": row["record_id"],
                    "category": "crossref_metadata",
                    "title": row["title"],
                    "url": f"https://api.crossref.org/works/{quote(doi, safe='')}",
                    "identifier": doi,
                    "usage_conditions": (
                        "Crossref public bibliographic metadata; "
                        "https://www.crossref.org/documentation/retrieve-metadata/"
                        "rest-api/rest-api-metadata-license-information/"
                    ),
                    "publish_raw": "true",
                }
            )
    return records


def web_records() -> list[dict[str, str]]:
    path = ROOT / "references" / "web_source_manifest.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot-id",
        default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot_dir = ROOT / "data" / "raw" / "external" / args.snapshot_id
    publish_dir = ROOT / "data" / "raw" / "published_sources" / args.snapshot_id
    if snapshot_dir.exists() or publish_dir.exists():
        raise FileExistsError(f"snapshot already exists: {args.snapshot_id}")
    snapshot_dir.mkdir(parents=True)
    publish_dir.mkdir(parents=True)

    acquired_at = datetime.now(UTC).isoformat()
    ledger: list[dict[str, object]] = []
    for record in [*literature_records(), *web_records()]:
        extension = Path(record["url"].split("?", 1)[0]).suffix or ".bin"
        if record["category"] == "crossref_metadata":
            extension = ".json"
        filename = f"{safe_name(record['source_id'])}{extension}"
        publishable = record["publish_raw"].lower() == "true"
        destination = (publish_dir if publishable else snapshot_dir) / filename
        entry: dict[str, object] = {
            **record,
            "retrieved_at_utc": acquired_at,
            "request_method": "GET",
            "request_headers": {"User-Agent": USER_AGENT, "Accept": "*/*"},
            "completeness": "failed",
        }
        try:
            content, response = download(record["url"])
            destination.write_bytes(content)
            entry.update(
                {
                    "storage_path": str(destination.relative_to(ROOT)),
                    "file_size_bytes": len(content),
                    "sha256": sha256(content),
                    "http_status": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "completeness": "complete response body",
                }
            )
        except requests.RequestException as error:
            entry["error"] = str(error)
        ledger.append(entry)

    ledger_path = ROOT / "data" / "metadata" / f"research_sources_{args.snapshot_id}.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    failed = [entry for entry in ledger if entry["completeness"] == "failed"]
    print(
        json.dumps(
            {
                "ledger": str(ledger_path.relative_to(ROOT)),
                "complete": len(ledger) - len(failed),
                "failed": len(failed),
            }
        )
    )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
