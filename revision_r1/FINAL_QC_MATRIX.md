# FINAL_QC_MATRIX (R1)

| Area | Status | Evidence |
|---|---|---|
| Baseline preserved (tag `crst-submitted-v1`, SHA manifest, fallback DOCX) | done | PHASE_00_PROJECT_RECOVERY.md, baseline/ |
| Original outputs untouched (`results/generated`, `checkpoints/dt_0p5h`) | done | R1 writes only to results/r1, figures/r1, manuscript/r1 |
| Raw public data persisted with ledger (URL, UTC time, size, SHA-256, terms) | done | data/raw/, acquisition ledger |
| Event metric pre-specified and convergence-tested | done | EVENT_METRIC_SPECIFICATION.md, NUMERICAL_CONVERGENCE_AUDIT.md |
| Numerical vs optimiser convergence vs physical validation kept separate | done | PARETO_RELIABILITY_AUDIT.md, PHYSICAL_BENCHMARK_AUDIT.md |
| Constructability inside optimisation; equal budgets; 5 seeds | done | CONSTRAINED_OPTIMIZATION_AUDIT.md |
| Robustness with revised metric | done | ROBUSTNESS_AUDIT.md |
| Synthetic vs JMA forcing separated; JMA not validation | done | WEATHER_FORCING_AUDIT.md |
| Semantic code audit | done | SEMANTIC_CODE_AUDIT.md |
| Figures from canonical CSVs (PNG, RGB TIFF 1000 dpi, PDF, SVG + data CSV) | done | figures/r1, results/r1/figure_data |
| Manuscript values generated from CSVs (no hard-coded results) | done | scripts/r1_build_manuscript.py |
| Abstract <= 250 words, 3-5 highlights <= 85 characters, line numbers, OMML equations | done | TEXT_FIGURE_TABLE_CONSISTENCY.md |
| All figures/tables cited in order and placed inline after first citation | done | TEXT_FIGURE_TABLE_CONSISTENCY.md |
| Vancouver order, no orphan references, DOI records checked | done | REFERENCE_AUDIT_R1.md/.csv |
| Tracked DOCX (red additions, blue strikethrough deletions) with content identical to clean | done (vs fallback baseline) | check "Tracked minus deletions == clean text" |
| Editable tables DOCX, editable figures PPTX (16:9, one per slide) | done | manuscript/r1 |
| Lint (`ruff check src scripts tests`) and tests (`pytest`) | done | local run |
| Reviewer-driven analyses (factor attribution, roof length, budgets, threshold check) | done | results/r1/review |
| Hostile review | done | HOSTILE_REVIEW_FINAL.md |
| Author metadata (affiliation, funding, competing interests, CRediT) | author-pending (completed locally by the author; not a QC failure) | 5 REQUIRED placeholders |
| Editor/Reviewer comments, point-by-point response, response matrix | done (37 comments; kept outside git as confidential) | private/r1_response/ (scripts/r1_response.py) |
| Tracked DOCX against Editorial Manager file | done (title page excluded) | PHASE_00_PROJECT_RECOVERY.md update |
| `make all` (submitted pipeline) | not re-run by design: it regenerates historical outputs; R1 is reproduced by `make r1` | Makefile |
| Submission / editor contact / merge | not done (not authorised) | - |
