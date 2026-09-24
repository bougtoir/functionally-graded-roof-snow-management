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
ENDPOINT = "https://www.data.jma.go.jp/risk/obsdl/show/table"
TERMS = "https://www.jma.go.jp/jma/kishou/info/coment.html"
ELEMENTS = [["201", ""], ["101", ""], ["503", ""], ["501", ""]]
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/140.0 Safari/537.36 graded-roof-snow-research/0.1"
)


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot-id",
        default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
    )
    parser.add_argument("--pause-seconds", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = yaml.safe_load((ROOT / "config" / "production.yaml").read_text())
    destination = ROOT / "data" / "raw" / "jma" / args.snapshot_id
    if destination.exists():
        raise FileExistsError(f"snapshot already exists: {destination}")
    destination.mkdir(parents=True)
    records: list[dict[str, object]] = []
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Referer": "https://www.data.jma.go.jp/risk/obsdl/",
            "Origin": "https://www.data.jma.go.jp",
        }
    )
    session.get("https://www.data.jma.go.jp/risk/obsdl/", timeout=60).raise_for_status()

    for station in config["jma"]["stations"]:
        for winter in config["jma"]["winters"]:
            payload = {
                "stationNumList": json.dumps([station["id"]]),
                "aggrgPeriod": "9",
                "elementNumList": json.dumps(ELEMENTS),
                "interAnnualType": "1",
                "ymdList": json.dumps(
                    [
                        winter,
                        winter + 1,
                        config["jma"]["season_start_month"],
                        config["jma"]["season_end_month"],
                        1,
                        30,
                    ]
                ),
                "optionNumList": "[]",
                "downloadFlag": "true",
                "rmkFlag": "1",
                "disconnectFlag": "1",
                "youbiFlag": "0",
                "fukenFlag": "0",
                "kijiFlag": "0",
                "csvFlag": "1",
                "jikantaiFlag": "0",
                "jikantaiList": "[]",
                "ymdLiteral": "1",
            }
            retrieved = datetime.now(UTC).isoformat()
            response = session.post(
                ENDPOINT,
                data=payload,
                timeout=180,
            )
            if not response.ok:
                raise RuntimeError(
                    f"JMA HTTP {response.status_code}: {response.text[:500]}"
                )
            content = response.content
            if response.headers.get("Content-Type", "").startswith("text/html"):
                raise RuntimeError(f"JMA returned HTML: {response.text[:500]}")
            decoded = content.decode("cp932")
            if "年月日時" not in decoded or len(content) < 1000:
                raise RuntimeError(
                    f"unexpected JMA response for {station['id']} winter {winter}"
                )
            stem = f"{station['id']}_winter_{winter}_{winter + 1}_hourly"
            raw_path = destination / f"{stem}.csv"
            utf8_path = destination / f"{stem}_utf8.csv"
            request_path = destination / f"{stem}_request.json"
            headers_path = destination / f"{stem}_headers.json"
            raw_path.write_bytes(content)
            utf8_path.write_text(decoded, encoding="utf-8")
            request_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            headers_path.write_text(
                json.dumps(dict(response.headers), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            records.append(
                {
                    "source_type": "JMA Past Weather Data Download hourly CSV",
                    "source_url": ENDPOINT,
                    "identifier": f"{station['id']}:{winter}-{winter + 1}",
                    "retrieved_at_utc": retrieved,
                    "acquisition_conditions": payload,
                    "storage_path": str(raw_path.relative_to(ROOT)),
                    "utf8_derivative_path": str(utf8_path.relative_to(ROOT)),
                    "request_path": str(request_path.relative_to(ROOT)),
                    "response_headers_path": str(headers_path.relative_to(ROOT)),
                    "file_size_bytes": len(content),
                    "sha256": sha256(content),
                    "usage_conditions": TERMS,
                    "completeness": "complete requested station-winter interval",
                }
            )
            time.sleep(args.pause_seconds)

    ledger = ROOT / "data" / "metadata" / f"jma_hourly_{args.snapshot_id}.json"
    ledger.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"records": len(records), "ledger": str(ledger.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
