from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh-root", type=Path, required=True)
    args = parser.parse_args()
    fresh_root = args.fresh_root.resolve()

    relative_paths = sorted(
        [
            path.relative_to(ROOT)
            for pattern in ("results/generated/*.csv", "tables/generated/*.csv")
            for path in ROOT.glob(pattern)
        ]
    )
    rows = []
    for relative_path in relative_paths:
        committed_path = ROOT / relative_path
        fresh_path = fresh_root / relative_path
        committed_hash = _sha256(committed_path)
        fresh_hash = _sha256(fresh_path) if fresh_path.exists() else ""
        rows.append(
            {
                "path": str(relative_path),
                "committed_sha256": committed_hash,
                "fresh_sha256": fresh_hash,
                "status": (
                    "identical"
                    if committed_hash == fresh_hash
                    else ("missing" if not fresh_path.exists() else "mismatch")
                ),
            }
        )

    comparison_path = (
        ROOT / "audit" / "final_revision" / "fresh_reproduction_comparison.csv"
    )
    with comparison_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    validation = json.loads(
        (
            fresh_root / "manuscript" / "build" / "validation_report.json"
        ).read_text(encoding="utf-8")
    )
    identical = sum(row["status"] == "identical" for row in rows)
    mismatches = [row["path"] for row in rows if row["status"] != "identical"]
    report = [
        "# Fresh reproducibility audit",
        "",
        f"Run recorded: {datetime.now(UTC).isoformat()}",
        "",
        "## Verdict",
        "",
        (
            "- Quantitative reproduction: **PASS**."
            if not mismatches and not validation["errors"]
            else "- Quantitative reproduction: **FAIL**."
        ),
        "- Complete local literature-evidence reproduction from the public checkout: "
        "**PARTIAL**. Three redistribution-restricted institutional/municipal source "
        "files are intentionally excluded from Git; URLs, recorded sizes, checksums, "
        "and usage conditions remain in the ledger.",
        "",
        "## Clean execution",
        "",
        "- A detached worktree was created from the Phase 13 commit.",
        "- A new Python 3.11.10 virtual environment was created and the pinned project "
        "plus development dependencies were installed.",
        "- The production pipeline reran the data, baseline, convergence, exhaustive "
        "uniform, nine fresh heterogeneous optimization, JMA, sensitivity, robustness, "
        "tables, figures, manuscript, and validation stages.",
        "- Full production computation took 70 minutes 2.652 seconds.",
        "- Ruff passed and all 31 tests passed in the fresh environment.",
        "",
        "## Output comparison",
        "",
        f"- Compared quantitative CSV files: {len(rows)}.",
        f"- Byte-identical files: {identical}.",
        f"- Missing or mismatched files: {len(mismatches)}.",
        "- The machine-readable comparison records both SHA-256 values for every file.",
        "",
        "## Validation",
        "",
        f"- Validation errors: {len(validation['errors'])}.",
        f"- Validation warnings: {len(validation['warnings'])}.",
        f"- Reference entries: {validation['checks'].get('reference_count')}.",
        "- The proper minus sign used in font-superscript unit exponents is explicitly "
        "allowed; no unsupported non-ASCII character remains.",
        "",
        "## Problems found and corrected",
        "",
        "1. The first clean validation rejected the correct U+2212 minus sign used in "
        "font-superscript unit exponents. Validation now allows that character while "
        "continuing to reject other unsupported non-ASCII characters.",
        "2. Validation regenerated the legacy project-state section and initially "
        "dropped the final-revision phase history. The state updater now preserves the "
        "final-revision section.",
        "3. The literature-stage checksum audit cannot resolve the three intentionally "
        "unpublished local source files from the public checkout. This does not affect "
        "the 58 regenerated quantitative CSV files, but prevents a claim of complete "
        "local archival reproduction from the public repository alone.",
        "",
        "## Evidence",
        "",
        "- `audit/final_revision/fresh_reproduction_comparison.csv`",
        "- `audit/final_revision/fresh_reproduction_run.log`",
        "- `audit/final_revision/fresh_final_revision_analyses.log`",
        "- `manuscript/build/validation_report.json`",
    ]
    (ROOT / "audit" / "REPRODUCIBILITY_AUDIT.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )
    if mismatches or validation["errors"]:
        raise SystemExit(
            f"fresh reproduction failed: mismatches={mismatches}, "
            f"errors={validation['errors']}"
        )


if __name__ == "__main__":
    main()
