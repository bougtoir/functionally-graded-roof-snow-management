"""Audit references cited in the R1 manuscript against stored raw records."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
from docx import Document

RAW = sorted(Path("data/raw/published_sources").rglob("*.json"))


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(t).lower())


def crossref_title(rid: str) -> tuple[str, str]:
    for p in RAW:
        if p.stem.lower() == rid.lower():
            try:
                msg = json.loads(p.read_text()).get("message", {})
                return " ".join(msg.get("title", [""])), str(p)
            except Exception:  # noqa: BLE001
                return "", str(p)
    return "", ""


def main(docx: Path, out: Path) -> pd.DataFrame:
    db = pd.concat(
        [
            pd.read_csv("references/literature_database.csv"),
            pd.read_csv("references/references_r1_additional.csv"),
        ]
    ).set_index("record_id")
    d = Document(docx)
    text = "\n".join(p.text for p in d.paragraphs)
    body = text.split("\nReferences\n")[0]
    refs = [p.text for p in d.paragraphs if re.match(r"\[\d+\] ", p.text)]
    cited = sorted({int(n) for g in re.findall(r"\[([\d,]+)\]", body) for n in g.split(",")})
    first = []
    for g in re.findall(r"\[([\d,]+)\]", body):
        for n in g.split(","):
            if int(n) not in first:
                first.append(int(n))
    rows = []
    for i, r in enumerate(refs, 1):
        title_in_ref = r
        rid = next((k for k in db.index if norm(db.loc[k, "title"]) in norm(title_in_ref)), "")
        cr, src = crossref_title(rid) if rid else ("", "")
        doi = str(db.loc[rid, "doi_or_identifier"]) if rid else ""
        rows.append(
            {
                "number": i,
                "record_id": rid,
                "identifier": doi,
                "cited_in_text": i in cited,
                "crossref_record": src,
                "crossref_title_match": (norm(cr) == norm(db.loc[rid, "title"]))
                if cr
                else "no stored DOI record",
                "reference": r,
            }
        )
    a = pd.DataFrame(rows)
    a["order_of_first_appearance_ok"] = first == list(range(1, len(refs) + 1))
    a.to_csv(out, index=False)
    return a


if __name__ == "__main__":
    a = main(Path(sys.argv[1]), Path(sys.argv[2]))
    print(a.drop(columns="reference").to_string())
