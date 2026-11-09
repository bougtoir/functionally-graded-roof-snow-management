# REPRODUCIBILITY_AUDIT (R1)

## Environment
- Python venv `.venv` (Python 3.11); dependencies in `pyproject.toml`; numba not required by R1 code.
- Production configuration `config/production.yaml` (SHA-256 recorded in every optimiser `*_meta.json`).
- Hardware for the reported runs: 2 vCPU, 7 GB RAM; multiprocessing with 2 workers.

## Pipeline (run from repository root, in order)
| Step | Command | Outputs |
|---|---|---|
| Synthetic forcing summary | `.venv/bin/python scripts/r1_weather.py` (if present) | `results/r1/weather/` |
| Convergence | `.venv/bin/python scripts/r1_convergence.py` | `results/r1/convergence/` (selects dt) |
| Optimisation | `.venv/bin/python scripts/r1_optimize.py` | `results/r1/optimization/` (uniform exhaustive, continuous grid, 3 modes x 5 seeds) |
| Pareto analysis | `.venv/bin/python scripts/r1_analyze.py` | `results/r1/pareto/` incl. fine re-check |
| Robustness | `.venv/bin/python scripts/r1_robustness.py` | `results/r1/robustness/` |
| Event-definition sensitivity | `.venv/bin/python scripts/r1_event_sensitivity.py` | `results/r1/event_sensitivity/` |
| JMA scenarios | `.venv/bin/python scripts/r1_jma.py` | `results/r1/jma/` |
| Figures | `.venv/bin/python scripts/r1_figures.py` | `figures/r1/{png,tiff,vector}`, `results/r1/figure_data/` |
| Manuscript | `.venv/bin/python scripts/r1_build_manuscript.py` | `manuscript/r1/manuscript_R1_clean.docx` |
| Package | `.venv/bin/python scripts/r1_package.py` | supplement, cover letter, highlights, editable tables/figures, marked-up comparison |
| Reference audit | `.venv/bin/python scripts/r1_reference_audit.py manuscript/r1/manuscript_R1_clean.docx revision_r1/REFERENCE_AUDIT_R1.csv` | audit CSV |

`scripts/r1_chain.sh` runs robustness -> sensitivity -> JMA -> figures sequentially.

## Determinism
- All random draws are seeded (optimiser seeds 1701, 2903, 4517, 6007, 8191; robustness seed 7021; convergence design sample seeded in script).
- Synthetic forcing is deterministic and analytic (no random terms).
- Manuscript numbers are read from result CSVs at build time; no result value is typed into the manuscript text.

## Data provenance
- JMA daily observations: raw snapshots `data/raw/jma_daily/20260924T120000Z/`, processed `data/processed/jma_daily_observations.csv`.
- Official Japanese context sources: `data/raw/japan_context/20261109/`.
- Crossref records: `data/raw/published_sources/*/`, `data/raw/reviewer_doi/`.
- Acquisition ledger with URL, UTC retrieval time, size and SHA-256: `data/metadata/acquisition_ledger.csv`.

## Separation of original and revised analysis
Submitted state: tag `crst-submitted-v1`, hashes `revision_r1/baseline/BASELINE_SHA256_MANIFEST.txt`. Original outputs in `results/generated/`, `results/reference_1h/`, `checkpoints/dt_0p5h/` are untouched; R1 outputs live in `results/r1/`, `figures/r1/`, `manuscript/r1/`.

## Runtimes observed
Convergence ~ 1 h; optimisation 15 runs 58-138 s each plus uniform grids; Pareto fine re-check minutes; robustness (211 designs x 250 draws x 3 winters) ~ 1.5-2 h on 2 cores.
