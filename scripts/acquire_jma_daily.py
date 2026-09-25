from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://www.data.jma.go.jp/stats/etrn/view/daily_s1.php"
TERMS = "https://www.jma.go.jp/jma/kishou/info/coment.html"
USER_AGENT = (
    "graded-roof-snow-research/0.1 "
    "(https://github.com/bougtoir/functionally-graded-roof-snow-management)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot-id",
        default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
    )
    parser.add_argument("--pause-seconds", type=float, default=2.0)
    return parser.parse_args()


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(
        (ROOT / "config" / "production.yaml").read_text(encoding="utf-8")
    )
    destination = ROOT / "data" / "raw" / "jma_daily" / args.snapshot_id
    if destination.exists():
        raise FileExistsError(f"snapshot already exists: {destination}")
    destination.mkdir(parents=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    records: list[dict[str, object]] = []

    for station in config["jma"]["stations"]:
        for winter in config["jma"]["winters"]:
            months = [(winter, 11), (winter, 12), *[(winter + 1, m) for m in range(1, 5)]]
            for year, month in months:
                params = {
                    "prec_no": station["prec_no"],
                    "block_no": station["block_no"],
                    "year": str(year),
                    "month": f"{month:02d}",
                    "day": "",
                    "view": "p1",
                }
                retrieved = datetime.now(UTC).isoformat()
                response = session.get(ENDPOINT, params=params, timeout=120)
                response.raise_for_status()
                content = response.content
                if len(content) < 5000 or b"table" not in content.lower():
                    raise RuntimeError(
                        f"unexpected JMA daily response for {station['id']} {year}-{month:02d}"
                    )
                stem = f"{station['id']}_{year}_{month:02d}_daily"
                raw_path = destination / f"{stem}.html"
                request_path = destination / f"{stem}_request.json"
                headers_path = destination / f"{stem}_headers.json"
                raw_path.write_bytes(content)
                request_path.write_text(
                    json.dumps(params, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                headers_path.write_text(
                    json.dumps(dict(response.headers), ensure_ascii=False, indent=2)
                    + "\n",
                    encoding="utf-8",
                )
                records.append(
                    {
                        "source_type": "JMA Historical Weather Data Search daily HTML",
                        "source_url": response.url,
                        "identifier": f"{station['id']}:{year}-{month:02d}",
                        "retrieved_at_utc": retrieved,
                        "acquisition_conditions": params,
                        "storage_path": str(raw_path.relative_to(ROOT)),
                        "request_path": str(request_path.relative_to(ROOT)),
                        "response_headers_path": str(headers_path.relative_to(ROOT)),
                        "file_size_bytes": len(content),
                        "sha256": sha256(content),
                        "usage_conditions": TERMS,
                        "completeness": "complete requested station-month daily table",
                    }
                )
                time.sleep(args.pause_seconds)

    ledger = ROOT / "data" / "metadata" / f"jma_daily_{args.snapshot_id}.json"
    ledger.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"records": len(records), "ledger": str(ledger.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
