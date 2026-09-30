# Reproducibility and provenance trace

## End-to-end trace

`audit/final_revision/provenance_trace.csv` maps each analysis from persistent
raw data or frozen configuration through processing code, canonical result
files, figures/tables, and the manuscript generator. A SHA-256 inventory of
the current canonical inputs and generated CSVs is recorded in
`audit/final_revision/canonical_artifact_checksums.csv`.

## JMA quantitative inputs

The official daily HTML pages used for quantitative supplementary scenarios are
retained under the timestamped JMA raw-data directory. The acquisition ledger
records their source requests, retrieval time, saved path, byte count,
SHA-256, and usage conditions. All ledger entries pointing to the retained JMA
snapshot pass local checksum verification.

The pipeline parses retained HTML into
`data/processed/jma_daily_observations.csv`, constructs station-winter forcing,
and writes `results/generated/jma_daily_evaluation.csv`. Table 9 and manuscript
text are generated from that result. Ground observations are not described as
roof-load measurements.

## Configuration and seeds

- The analysis freeze is `analysis_freeze.yaml`.
- Production physical, numerical, optimizer, robustness, and decision settings
  are in `config/production.yaml`.
- Parameter evidence status and required sensitivity checks are in
  `references/parameter_sources.csv`.
- The three optimizer seeds and all nine expensive checkpoints are retained.
- The robustness seed, sample count, quantile, and perturbation magnitudes are
  configuration values rather than manuscript literals.

## Hard-coded and manual-result audit

No audited headline result literal (`3210.6`, `3913.3`, `6417.0`, `4200.4`, or
`226.0`) occurs in executable Python. Manuscript values are read from generated
CSV files. Scientific constants and model assumptions are configured or
identified in the parameter-source database; the standard acceleration of
gravity is explicitly identified as a standard constant.

The repository contains legacy narrative audits and manuscript files generated
before this final revision. They are not treated as final outputs. Phase 16
must rebuild the manuscript, manifest, validation report, and submission ZIP
from the revised pipeline.

## Unavailable historical records

The acquisition ledger currently distinguishes checksum-verified local files,
historical records not recovered into the public checkout, and one blocked
record with no retained path. Unavailable records are provenance disclosures,
not quantitative inputs or archived evidence. The final validation report must
use the regenerated ledger counts rather than older narrative counts.

## Gate

Status: PASS for traceability. No corrupt retained quantitative input, missing
optimizer checkpoint, or embedded primary-result literal was found. Scientific
interpretation and stale final-document replacement remain open in later
phases.
