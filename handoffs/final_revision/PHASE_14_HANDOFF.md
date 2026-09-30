# Phase 14 handoff: fresh reproducibility

Status: complete with disclosed archival limitation

## Clean quantitative reproduction

- Created a detached worktree from the Phase 13 commit.
- Created a new Python 3.11.10 virtual environment and installed the pinned project and
  development dependencies.
- Reran the production pipeline without optimizer checkpoints, including 6,300 uniform
  designs and nine heterogeneous optimization runs.
- Reran the final-revision quantitative stages and regenerated the manuscript and
  submission package.
- Compared all 58 result and table CSV files: every file was byte-identical to the
  committed version.
- Ruff passed, all 31 tests passed, and final validation reported zero errors.

## Reproduction-discovered corrections

- Updated validation to permit the proper U+2212 minus sign only where the manuscript
  audit independently verifies font-superscript unit exponents.
- Updated reference validation for the current author-year bibliography.
- Updated the legacy project-state writer to preserve final-revision phase history.

## Disclosed limitation

The public checkout intentionally excludes three redistribution-restricted
institutional/municipal source files used only for literature evidence (JP02, JP03, and
JP09). Their URLs, sizes, checksums, and usage conditions remain in the acquisition
ledger, but the public checkout alone cannot rerun their local checksum audit.
Quantitative inputs and all 58 regenerated quantitative CSV files are unaffected.

## Evidence

- `audit/REPRODUCIBILITY_AUDIT.md`
- `audit/final_revision/fresh_reproduction_comparison.csv`
- `audit/final_revision/fresh_reproduction_run.log`
- `audit/final_revision/fresh_final_revision_analyses.log`
- `manuscript/build/validation_report.json`
