"""Append acquisition-ledger rows for persisted raw files (R1)."""
from __future__ import annotations

import csv
import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path

LEDGER = Path("data/metadata/acquisition_ledger.csv")


def append(topic, source_type, title, url, identifier, path, usage, completeness="complete response body", conditions="GET"):
    p = Path(path)
    data = p.read_bytes()
    with LEDGER.open("a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow([
            topic, source_type, title, url, identifier,
            datetime.fromtimestamp(p.stat().st_mtime, UTC).isoformat(), conditions, str(p),
            len(data), hashlib.sha256(data).hexdigest(), usage, completeness, "verified",
        ])


if __name__ == "__main__":
    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        if line.strip():
            append(*line.split("\t"))
