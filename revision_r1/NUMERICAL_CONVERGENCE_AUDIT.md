# NUMERICAL_CONVERGENCE_AUDIT (R1)

Machine-readable: `results/r1/convergence/convergence_runs.csv` (per design × winter × resolution), `convergence_summary.csv`, `production_dt_choice.json`. Script: `scripts/r1_convergence.py`. Criteria were fixed in `EVENT_METRIC_SPECIFICATION.md` §5 before the runs.

## Scope
- Panel: 132 constructable uniform roofs + 60 constructable graded roofs (seed 9001) × 3 synthetic winters; 543 unique design–winter pairs after duplicate removal.
- Temporal: dt = 1, 0.5, 0.25, 0.125 h against dt_ref = 0.0625 h (N = 24).
- Spatial: N = 48 and 96 (segment lengths scaled, dt = 0.25 h) against the same reference.
- Metrics: L_max, S_event,max, S_1h,max, total shed, event count, mass balance.

## Results (from `convergence_summary.csv`)
| dt (h) | N | agree L_max | agree S_event,max | agree S_1h | agree total shed | event count ±1 | p95 rel. diff S_event,max |
|---|---|---|---|---|---|---|---|
| 1.0 | 24 | 0.982 | 0.959 | 0.971 | 0.987 | 0.996 | 2.9 % |
| 0.5 | 24 | 0.989 | 0.982 | 0.985 | 0.991 | 0.998 | 0.63 % |
| 0.25 | 24 | 0.998 | 0.998 | 0.996 | 1.000 | 1.000 | 0.25 % |
| 0.125 | 24 | 1.000 | 1.000 | 0.998 | 1.000 | 0.998 | 0.10 % |
| 0.25 | 48 | 0.996 | 0.996 | 0.994 | 0.998 | 1.000 | 0.29 % |
| 0.25 | 96 | 0.996 | 0.996 | 0.994 | 0.998 | 1.000 | 0.29 % |

Mass-balance error was 0 to machine precision (< 1e-6 kg m⁻¹) in every run.

## Decision
Every tested step met the pre-specified rule; the rule selects the coarsest, **dt = 1 h**, for optimisation and robustness. Because a small number of designs that sit on a failure threshold change by up to 1.3 t m⁻¹ at 1 h (threshold-boundary sensitivity: a release occurs or not within a winter), all final nondominated designs are re-evaluated at dt = 0.0625 h and N = 48 (pre-specified before optimisation; results in `PARETO_RELIABILITY_AUDIT.md`).

## Comparison with the submitted scheme
The submitted per-step endpoint halved when dt halved (uniform 40° smooth roof: 40.0 → 20.0 → 10.0 kg m⁻¹ for 1, 0.5, 0.25 h in `severe_inland`) while the revised event endpoint is unchanged (1599.9 / 1599.5 / 1599.5 kg m⁻¹) and the 1-h window value is unchanged (79.9 kg m⁻¹).

## Distinctions
Numerical convergence (this file) ≠ physical validation (none available; `PHYSICAL_EVIDENCE_GAP.md`) ≠ optimiser convergence (`PARETO_RELIABILITY_AUDIT.md`).
