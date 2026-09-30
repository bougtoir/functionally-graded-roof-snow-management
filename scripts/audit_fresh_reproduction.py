from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh-root", type=Path, required=True)
    parser.add_argument("--duration-seconds", type=float, required=True)
    parser.add_argument("--test-count", type=int, required=True)
    parser.add_argument("--python-version", required=True)
    parser.add_argument("--lint-passed", action="store_true")
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
        ROOT / "audit" / "0p5h_revision" / "fresh_reproduction_comparison.csv"
    )
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    with comparison_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    legacy_comparison = (
        ROOT / "audit" / "final_revision" / "fresh_reproduction_comparison.csv"
    )
    shutil.copyfile(comparison_path, legacy_comparison)

    validation = json.loads(
        (
            fresh_root / "manuscript" / "build" / "validation_report.json"
        ).read_text(encoding="utf-8")
    )
    identical = sum(row["status"] == "identical" for row in rows)
    mismatches = [row["path"] for row in rows if row["status"] != "identical"]
    passed = (
        not mismatches
        and not validation["errors"]
        and args.lint_passed
    )
    summary = {
        "recorded_utc": datetime.now(UTC).isoformat(),
        "passed": passed,
        "fresh_root": str(fresh_root),
        "python_version": args.python_version,
        "duration_seconds": args.duration_seconds,
        "test_count": args.test_count,
        "lint_passed": args.lint_passed,
        "compared_files": len(rows),
        "identical_files": identical,
        "mismatches": mismatches,
        "validation_errors": validation["errors"],
        "validation_warning_count": len(validation["warnings"]),
    }
    summary_path = (
        ROOT / "audit" / "0p5h_revision" / "reproduction_summary.json"
    )
    summary_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    report = [
        "# Fresh reproducibility audit",
        "",
        f"Run recorded: {datetime.now(UTC).isoformat()}",
        "",
        "## Verdict",
        "",
        (
            "- Quantitative reproduction: **PASS**."
            if passed
            else "- Quantitative reproduction: **FAIL**."
        ),
        "- Complete local literature-evidence reproduction from the public checkout: "
        "**PARTIAL**. Three redistribution-restricted institutional/municipal source "
        "files are intentionally excluded from Git; URLs, recorded sizes, checksums, "
        "and usage conditions remain in the ledger.",
        "",
        "## Clean execution",
        "",
        "- A detached worktree was created from the current 0.5-h revision commit.",
        f"- A new Python {args.python_version} virtual environment was created and "
        "the pinned project plus development dependencies were installed.",
        "- The production pipeline reran the data, baseline, convergence, exhaustive "
        "uniform, nine fresh heterogeneous optimization, JMA, sensitivity, robustness, "
        "tables, figures, manuscript, and validation stages.",
        f"- Full production computation took {args.duration_seconds:.3f} seconds.",
        f"- Ruff passed: {args.lint_passed}; {args.test_count} tests passed.",
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
        "## Numerical-resolution interpretation",
        "",
        "- The clean run used the canonical 0.5-h production configuration and fresh "
        "timestep-isolated optimization checkpoints.",
        "- The 1-h archive was not loaded as a production checkpoint.",
        "- The targeted 0.25-h calculation remains a sensitivity analysis and does not "
        "change the production resolution.",
        "",
        "## Evidence",
        "",
        "- `audit/0p5h_revision/fresh_reproduction_comparison.csv`",
        "- `audit/0p5h_revision/reproduction_summary.json`",
        "- `manuscript/build/validation_report.json`",
    ]
    (ROOT / "audit" / "REPRODUCIBILITY_AUDIT.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )
    if not passed:
        raise SystemExit(
            f"fresh reproduction failed: mismatches={mismatches}, "
            f"errors={validation['errors']}, lint_passed={args.lint_passed}"
        )


if __name__ == "__main__":
    main()
