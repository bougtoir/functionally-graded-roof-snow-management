# Final CRST handoff

## Status

**CRST decision: GO after author-supplied placeholders are completed.**

No unresolved critical scientific, numerical, citation, or file-integrity
defect was found. Affiliation, postal address, funding, competing interests,
CRediT roles, originality, author approval, and the final generative-AI
responsibility statement remain for local author completion as requested.

## Attached-manuscript revision

The supplied pre-revision inline manuscript was used as the comparison
baseline. Its structure was preserved: 109 paragraphs, 9 editable Tables, and
9 inline Figures. The canonical 0.5-hour manuscript updates the Abstract,
Methods, Results, Discussion, Limitations, Conclusions, and all numerical
Tables while retaining the prior literature positioning, notation corrections,
claim limits, author placeholders, and CRST organization.

The principal 1-hour to 0.5-hour changes are recorded in
`audit/0p5h_revision/OLD_VS_NEW_PRIMARY_AUDIT.md`. The central conclusion
changed in degree but not direction:

- the uniform set still has 2 unique objective pairs;
- the joint set has 6 unique pairs, including 4 intermediate pairs absent from
  the uniform set under the same objective caps;
- this does not establish front-wide superiority;
- no joint nondominated row passed every frozen post hoc constructability
  check;
- mapping the selected continuous profile changed Lmax by -98.28% and Smax by
  +537.47%, removing the nominal selected-profile advantage;
- nominal objective equivalence still did not imply robustness equivalence;
- JMA daily observations remain supplementary scenario forcing, not
  validation;
- the 0.5-hour production interval is the frozen numerical reference, while
  the targeted 0.25-hour check confirms remaining interval sensitivity.

## Analyses rerun or preserved

- Preserved the frozen research question, outcomes, physical assumptions,
  forcing, parameter ranges, optimizer effort, seeds, robustness
  distributions, constraints, and decision rules.
- Used the completed canonical 0.5-hour baseline, exhaustive uniform,
  multi-seed heterogeneous, frontier, constructability, robustness, JMA, and
  targeted 0.25-hour outputs.
- Regenerated Figures 1-9, Tables 1-9, the CRST manuscript, inline review copy,
  supplement, cover letter, editable Tables, editable Figures, and submission
  package from the canonical outputs.
- Preserved the archived 1-hour outputs only for the explicit old-versus-new
  audit.
- Did not start a new optimizer run or broaden the scientific analysis.

## Verification

| Check | Status |
|---|---|
| `manuscript_values.csv` | PASS: 65/65 rows |
| Manuscript-number consistency | PASS |
| Figures | PASS: 9/9 in PNG, TIFF, EPS, PDF, and SVG |
| Tables | PASS: 9/9 |
| References and citations | PASS |
| Reviewer-style scientific audit | PASS with limitations retained |
| Checkpoint integrity | PASS: 9/9 |
| Ruff | PASS |
| Pytest | PASS: 34 tests |
| Pipeline validation | PASS: 0 errors |
| CRST ZIP integrity | PASS |

The checkpoint-based regeneration is the final reproducibility evidence for
this finishing pass. A detached full optimizer rerun is not claimed.

## Final CRST files

- `manuscript/manuscript_CRST_final_0p5h.docx`
- `manuscript/manuscript_CRST_inline_final_0p5h.docx`
- `manuscript/cover_letter_CRST_final.docx`
- `manuscript/supplementary_material_CRST.docx`
- `manuscript/editable_tables_CRST.docx`
- `manuscript/editable_figures_CRST.pptx`
- `manuscript/highlights_CRST.txt`
- `manuscript/CRST_submission_checklist.md`
- `manuscript/CRST_scope_fit.md`
- `submission/CRST_submission_package_final.zip`
- `submission/CRST_submission_manifest.csv`
- `manuscript_values.csv`
- `audit/FINAL_AUDIT.md`
- `audit/FINAL_CRST_REVIEW.md`
- `audit/FABRICATION_AUDIT_FINAL.md`
- `audit/NUMERICAL_CONSISTENCY_FINAL.md`
- `references/REFERENCE_AUDIT_FINAL.csv`

## Reproduction command

The complete pipeline entry point is:

```bash
make all PYTHON=.venv/bin/python
```

For this final manuscript-only finishing pass, the executed path was:

```bash
.venv/bin/python scripts/run_pipeline.py manuscript
.venv/bin/python scripts/run_pipeline.py validate
```
