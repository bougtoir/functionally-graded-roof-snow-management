# PHASE 00 — Project recovery (CRST-D-26-01129 major revision)

Recovered: 2026-11-09 (UTC+9).

1. **Canonical repository and branch.** `bougtoir/functionally-graded-roof-snow-management`; submitted state = `main` at merge commit `472807b` (PR #1, merged 2026-09-30). Revision work branch: `devin/1794200841-crst-major-revision`.
2. **Exact baseline commit.** `472807b` (immutable annotated tag `crst-submitted-v1`). File-level SHA-256 manifest of every tracked file: `revision_r1/baseline/BASELINE_SHA256_MANIFEST.txt`. Submitted manuscript copy used for the tracked-changes diff: `revision_r1/baseline/manuscript_CRST_submitted_v1.docx` (= `manuscript/manuscript_CRST_submission_final.docx`; to be replaced if the author supplies the file actually uploaded to Editorial Manager).
3. **Scientific configuration at submission.** `config/production.yaml`; roof 8.0 m × 1.0 m, 24 cells, dt = 0.5 h, NSGA-II population 48 × 45 generations × seeds 1701/2903/4517 for geometry, surface and joint modes; 6,300-design uniform map (30 slopes × 30 frictions × 7 adhesions); three synthetic 336-h winters.
4. **Input datasets.** JMA daily tables (Kutchan, Aomori, Shinjo, Takada; winters 2021–2023) under `data/raw/jma_daily/` with ledger `data/metadata/acquisition_ledger.csv`; published-source snapshots under `data/raw/published_sources/`.
5. **Primary and secondary outcomes at submission.** `L_max` (maximum roof snow mass, kg m⁻¹) and `S_max` (maximum mass shed within one numerical timestep, kg m⁻¹); secondary SSCI, total shed, event counts, intervention metrics, complexity.
6. **Existing outputs.** `results/generated/` (0.5-h production), `results/reference_1h/` (historical 1-h), `checkpoints/dt_0p5h/`, figures 1–9, tables 1–9, `submission/CRST_submission_package_FINAL.zip`.
7. **Known scientific limitations (now reviewer-confirmed).** `S_max` is defined per numerical timestep and failed the targeted 0.25-h check (uniform knee 40.0 → 20.0 kg m⁻¹; joint continuous knee 12.35 → 6.67 kg m⁻¹); constructability (segmenting, discrete classes) applied only after optimization; parameter values largely engineering assumptions; no physical validation.
8. **Reusable computations.** JMA raw/processed data, acquisition ledger, reference database, figure/table/docx utilities. The original optimizer runs are retained as historical evidence only.
9. **Analyses requiring revision.** Transport algorithm and shedding endpoint (timestep artefact), convergence study, constrained optimization, Pareto reliability, robustness, sensitivity, figures, manuscript, response letter.
10. **Deadline.** Revision due 2026-11-29.

Original analysis remains distinguishable: nothing under `results/generated/`, `results/reference_1h/` or `checkpoints/dt_0p5h/` is overwritten; revised outputs are written to `results/r1/` and `checkpoints/r1/`.
