# Phase 00 finishing handoff: state recovery

Status: complete

## Frozen scientific state

- Research question: unchanged.
- Primary outcomes: `L_max` and `S_max`, with `S_max` defined per simulation
  timestep.
- Roof discretization: 24 cells.
- Existing production timestep: 1.0 h.
- Finest frozen convergence reference: 0.5 h.
- Frozen relative tolerance: 0.08 for `L_max`, `S_max`, mean event count, and
  mean SSCI.
- Uniform comparator: exhaustive 30 x 30 x 7 grid (6,300 designs).
- Heterogeneous optimizer: NSGA-II, population 48, 45 generations, seeds 1701,
  2903, and 4517, with four profile control points.
- Synthetic forcing: three deterministic 336-h scenarios from
  `config/production.yaml`.
- JMA forcing: daily station-winter scenarios retained as supplementary forcing
  and not converted to synthetic subdaily observations.

## Canonical state and provenance

- Configuration: `config/production.yaml`.
- Freeze: `analysis_freeze.yaml`.
- Deviations: `analysis_deviations.md`.
- Generated quantitative outputs: `results/generated/*.csv`.
- Optimizer checkpoints: `checkpoints/*.pkl`.
- Parameter sources: `references/parameter_sources.csv`.
- Reference audit: `references/final_revision_reference_audit.csv`.
- Acquisition ledger: `data/metadata/acquisition_ledger.csv`.
- Manuscript-number provenance: `audit/final_revision/number_provenance.csv`.
- Figure/table/manuscript generation: `src/graded_roof/reporting.py` and
  `src/graded_roof/manuscript.py`.
- Pipeline entry point: `scripts/run_pipeline.py`.
- Final-revision analyses: `scripts/run_final_revision_analyses.py`.

Every manuscript result is generated from the quantitative CSV files or
reference audit rather than entered independently into the DOCX.

## Preserved 1-hour reference

Before changing production resolution, all 48 current generated CSV files and
the production configuration were copied to `results/reference_1h/`.
`results/reference_1h/SHA256SUMS.txt` records their SHA-256 hashes. The archive
is read-only reference evidence for old-versus-new comparison; it is not a
second analysis tree.

## Required 0.5-hour change

The selected uniform, continuous-joint, and mapped-joint designs failed the
frozen four-metric criterion at 1 h when compared with the 0.5-h reference.
The finishing pass therefore moves synthetic production to 0.5 h without
changing objectives, forcing totals, parameter ranges, optimizer effort,
seeds, constraints, or reporting definitions.

The existing 1-h optimizer checkpoints cannot be reused for 0.5-h production.
New checkpoints must be isolated by timestep and verified against the current
configuration before resumption.
