# Changes available for the point-by-point response (R1)

This is not a response letter. Reviewer comments have not been supplied, so no comment is reproduced or paraphrased here. Once the decision letter is available, each comment will be mapped to the rows below or marked as not yet addressed.

| Change | Manuscript location (clean R1) | Evidence file |
|---|---|---|
| Physical event metric S_event,max replaces per-timestep S_max (legacy retained as diagnostic) | 2.2, Eq. 3, Fig. 1b, 2.8 | EVENT_METRIC_SPECIFICATION.md |
| Exact threshold-crossing times, work-energy runout, continuous forcing integration | 2.1, 2.3, Eqs. 1-2 | SEMANTIC_CODE_AUDIT.md |
| Pre-specified numerical convergence study (dt 1-0.0625 h; 24/48/96 cells) | 2.4, 3.1, Table 1, Fig. 3 | NUMERICAL_CONVERGENCE_AUDIT.md |
| Fine-resolution re-check of all front designs | 3.4 | PARETO_RELIABILITY_AUDIT.md |
| Constructability enforced inside NSGA-II; exhaustive constructable uniform set; equal budgets, 5 seeds | 2.5, 3.2-3.3, Table 2, Figs. 4-6 | CONSTRAINED_OPTIMIZATION_AUDIT.md |
| Hypervolume, normalised epsilon, matched comparisons, reference sensitivity, per-seed variability | 2.6, Table 2, Fig. 6 | PARETO_RELIABILITY_AUDIT.md |
| Event-definition and entrainment sensitivity | 2.7, 3.5, Table 3 | results/r1/event_sensitivity |
| Robustness re-run with new metric (friction, adhesion, density, snowfall, temperature) | 2.7, 3.6, Fig. 7 | ROBUSTNESS_AUDIT.md |
| JMA station-winters as scenario forcing (not validation) | 2.3, 3.7, Fig. 8 | WEATHER_FORCING_AUDIT.md |
| Japan heavy-snowfall and Building Standards context from official sources | 1 (paragraphs 1-2), 4 | JAPAN_CONTEXT_EVIDENCE.md, JAPAN_REGULATORY_MATRIX.csv |
| Parameter provenance and explicit non-validation statement | Table S1, 4.1-4.2 | PHYSICAL_PARAMETER_PROVENANCE.csv, PHYSICAL_BENCHMARK_AUDIT.md, PHYSICAL_EVIDENCE_GAP.md |
| Hydrology / rain-on-snow limitations | 4.1 | PHYSICAL_EVIDENCE_GAP.md |
| Title, abstract, highlights, conclusions narrowed (no superiority claim) | Title page, Abstract, 5 | HOSTILE_REVIEW_FINAL.md |
| Reproducibility: `make r1`, raw snapshots, acquisition ledger | Data availability, S3 | REPRODUCIBILITY_AUDIT.md |
