# Final CRST finishing handoff

## Decision

**GO after the author completes the approved placeholders and submission
declarations.**

The canonical scientific analysis remained frozen. No optimizer, Monte Carlo,
JMA, or new sensitivity run was started. No unresolved critical scientific,
numerical, citation, formatting, or package-integrity defect remains.

## Finishing changes

- Calibrated the title, Abstract, Discussion, Conclusions, cover letter, and
  highlights to describe nominal expansion of the modeled trade-off set without
  claiming practical superiority, safety, validation, or convergence beyond
  the 0.5-h production reference.
- Reframed continuous-to-discrete mapping as objective-space movement. The
  mapped selected point moves toward the low-retention, high-release shedding
  regime and is not presented as a constrained optimum.
- Clarified that the failed targeted 0.25-h check compares the 0.5-h production
  outcomes with 0.25-h reevaluations. No release-rate endpoint or finer
  production analysis was added.
- Updated Figure 4, Figure 6, and Table 3 wording and regenerated Figures 1-9
  and Tables 1-9 once from the canonical outputs.
- Created the requested submission-final filenames and final CRST ZIP.

## Numerical consistency

No incorrect canonical numerical result was found. The mapping arithmetic was
independently rechecked:

- Lmax: -4469.093535562355 kg m-1 (-98.27857106412374%).
- Smax: +66.00002741316608 kg m-1 (+537.4694412764242%).

The only inconsistency corrected in this pass was wording that obscured which
rows in the 0.25-h audit represented the production-versus-reference
comparison.

## Gates

| Gate | Status |
|---|---|
| `manuscript_values.csv` | PASS: 65/65 rows |
| Manuscript-number consistency | PASS |
| Canonical mapping arithmetic | PASS |
| Figures | PASS: 9/9 in PNG, TIFF, EPS, PDF, and SVG |
| Tables | PASS: 9/9 |
| Figure/table visual inspection | PASS |
| References and citations | PASS: 22/22 verified |
| Fabrication and provenance audit | PASS |
| Final hostile CRST review | PASS |
| CRST format and language audit | PASS |
| Ruff | PASS |
| Pytest | PASS: 34 tests |
| Pipeline validation | PASS: 0 errors |
| CRST ZIP integrity | PASS: 83 files |

Four intended warnings remain: approved author/declaration placeholders,
unresolved manual submission-checklist items, and non-quantitative source leads
that were not retained locally. Quantitative inputs and redistributable
evidence used by the study have verified snapshots.

## Final files

- `manuscript/manuscript_CRST_submission_final.docx`
- `manuscript/manuscript_CRST_inline_final_0p5h.docx`
- `manuscript/cover_letter_CRST_submission_final.docx`
- `manuscript/supplementary_material_CRST_submission_final.docx`
- `manuscript/editable_tables_CRST.docx`
- `manuscript/editable_figures_CRST.pptx`
- `manuscript/highlights_CRST.txt`
- `manuscript/CRST_submission_checklist_final.md`
- `manuscript/CRST_scope_fit_final.md`
- `audit/FINAL_FINISHING_AUDIT.md`
- `audit/FINAL_CRST_REVIEW.md`
- `audit/FABRICATION_AUDIT_FINAL.md`
- `audit/NUMERICAL_CONSISTENCY_FINAL.md`
- `references/REFERENCE_AUDIT_FINAL.csv`
- `figures/png/`
- `figures/tiff/`
- `figures/vector/`
- `tables/generated/`
- `manuscript_values.csv`
- `submission/CRST_submission_manifest.csv`
- `submission/CRST_submission_package_FINAL.zip`

## Exact finishing build and verification commands

```bash
.venv/bin/python scripts/run_pipeline.py tables
.venv/bin/python scripts/run_pipeline.py figures
.venv/bin/python scripts/run_pipeline.py manuscript
.venv/bin/python scripts/targeted_finalize.py --stage all
.venv/bin/python scripts/run_pipeline.py validate
.venv/bin/python -m ruff check src scripts tests
.venv/bin/python -m pytest
```

The full scientific pipeline remains available as
`make all PYTHON=.venv/bin/python`, but it was intentionally not rerun during
this frozen-analysis finishing pass.

## Git

Finishing implementation commit: `TO_BE_RECORDED_AFTER_COMMIT`.
