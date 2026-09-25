# Fresh reproducibility audit

## Verdict

- Quantitative reproduction: **PASS**.
- Complete local literature-evidence reproduction from the public checkout: **PARTIAL**. Three redistribution-restricted institutional or municipal source files are intentionally excluded from Git; URLs, recorded sizes, checksums, and usage conditions remain in the ledger.

## Clean execution

- A detached worktree and new Python 3.11.10 virtual environment were created from the Phase 13 commit.
- The production computation reran the complete quantitative pipeline in 70 minutes 2.652 seconds.
- Ruff passed and all 32 current tests pass.
- All 58 result and table CSV files are byte-identical to the committed outputs; the machine-readable comparison records both SHA-256 values.
- Validation reports zero errors and four intended manual/provenance warnings.

## Reproduction-discovered corrections

- Validation now permits the proper U+2212 minus sign used in audited font-superscript unit exponents while rejecting other unsupported non-ASCII characters.
- Reference validation now follows the current CRST author-year format.
- The legacy state updater preserves the final-revision phase history.
