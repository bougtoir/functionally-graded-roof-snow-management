"""Assemble the R1 revision package ZIP with a SHA-256 manifest."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

OUT = Path("submission/r1")
ITEMS = {
    "01_manuscript": [
        "manuscript/r1/manuscript_R1_clean.docx",
        "manuscript/r1/manuscript_R1_tracked.docx",
    ],
    "02_letters": ["manuscript/r1/cover_letter_R1.docx", "manuscript/r1/highlights_R1.txt"],
    "03_tables": ["manuscript/r1/editable_tables_R1.docx"],
    "04_figures": sorted(str(p) for p in Path("figures/r1").rglob("*") if p.is_file())
    + ["manuscript/r1/editable_figures_R1.pptx"],
    "05_supplementary": ["manuscript/r1/supplementary_material_R1.docx"],
    "06_results": sorted(
        str(p)
        for p in Path("results/r1").rglob("*.csv")
        if "optimization" not in p.parts or p.name.endswith("evaluated.csv")
    )
    + sorted(str(p) for p in Path("results/r1").rglob("*.json")),
    "07_audits": sorted(
        str(p) for p in Path("revision_r1").glob("*") if p.is_file() and "INTERNAL" not in p.name
    ),
    "08_reproduction": ["Makefile", "config/production.yaml", "pyproject.toml"],
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    z = OUT / "R1_revision_package.zip"
    rows = ["folder,path,bytes,sha256"]
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder, files in ITEMS.items():
            for f in files:
                p = Path(f)
                zf.write(p, f"{folder}/{p.as_posix()}")
                rows.append(f"{folder},{p.as_posix()},{p.stat().st_size},{sha(p)}")
        zf.writestr("MANIFEST_SHA256.csv", "\n".join(rows) + "\n")
    (OUT / "R1_revision_package_manifest.csv").write_text("\n".join(rows) + "\n")
    print(z, z.stat().st_size, len(rows) - 1, "files")
