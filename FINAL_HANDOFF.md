# Final handoff

## Targeted finalization completed

- Preserved the frozen 0.5-hour canonical analysis and archived 1-hour results.
- Refreshed the literature audit after moving the five public source snapshots to
  tracked `data/raw/published_sources/` paths.
- Created and verified `manuscript_values.csv`: 65 important reported values,
  65 PASS, 0 FAIL. Each row identifies the manuscript location, canonical source,
  source locator, derivation, generating code, and matched manuscript fragment.
- Regenerated all nine manuscript Tables and all nine Figures exactly once from
  the canonical result files. All table CSV, PNG, and TIFF checksums agreed with
  the pre-regeneration files. Vector files were regenerated and changed only at
  the serialized-file level.
- Regenerated the manuscript, inline review copy, supplement, cover letter,
  editable tables, editable figures, and CRST package.
- Verified manuscript-to-ledger-to-canonical-result consistency, table and figure
  completeness, ordered citations, all 22 reference titles, local source status,
  and local source-file existence.
- Produced an author-anonymized IJPE manuscript and IJPE-targeted submission
  files without changing the scientific analysis.

## Verification status

| Item | Status |
|---|---|
| `manuscript_values.csv` | PASS: 65/65 rows |
| Figures regenerated | PASS: 9/9 in PNG, TIFF, EPS, PDF, and SVG |
| Tables regenerated | PASS: 9/9 |
| Manuscript-number consistency | PASS |
| References and citations | PASS |
| Ruff | PASS |
| Pytest | PASS: 34 tests |
| Existing pipeline validation | PASS: 0 errors |
| Targeted finalization audit | PASS |

## Intentionally discontinued

The interrupted fresh `make all` run was terminated and is not claimed as
reproduction evidence. Repository-wide hash freezing, repeated clean builds,
forensic hard-code searches, exhaustive traceability of non-manuscript
intermediates, duplicate fabrication audits, checksums for every intermediate,
release-level dependency certification, and new analysis were intentionally
not performed.

## Final submission files

- `manuscript/manuscript_IJPE_blinded_final.docx`
- `manuscript/title_page_IJPE.docx`
- `manuscript/supplementary_material_IJPE.docx`
- `manuscript/cover_letter_IJPE_final.docx`
- `manuscript/highlights_IJPE.docx`
- `manuscript/highlights_IJPE.txt`
- `manuscript/editable_tables_IJPE.docx`
- `manuscript/editable_figures_IJPE.pptx`
- `submission/IJPE_submission_package_final.zip`
- `manuscript_values.csv`
- `audit/TARGETED_FINALIZATION.md`

## Unresolved issue and submission decision

No unresolved critical scientific, numerical, citation, or file-integrity defect
was found. Before submission, the author must complete the affiliation, postal
address, funding, competing-interest, contribution, originality, exclusivity,
and author-approval statements on the separate title page and cover letter.

**IJPE decision: CONDITIONAL GO.** IJPE's stated scope emphasizes the
engineering-management interface and economic or financial consequences. This
manuscript includes multiobjective optimization and decision scenarios but no
explicit economic or financial model. Confirm scope with the editor before
submission, or select a journal whose scope directly covers computational roof
engineering. The scope concern is editorial, not a defect in the canonical
analysis.
