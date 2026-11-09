# Analysis deviations

## 2026-09-25: production timestep correction after frozen convergence audit

- Old production resolution: 24 cells and a 1.0-h timestep.
- Corrected production resolution: 24 cells and a 0.5-h timestep, the finest
  resolution in the frozen convergence grid.
- Reason: the selected uniform, continuous-joint, and mapped-joint designs
  failed the frozen four-metric 8% criterion at 1 h relative to 0.5 h.
- Preserved decisions: research question, outcomes and their definitions,
  weather totals, model equations, uniform grid, parameter ranges, constraints,
  population, generations, seeds, robustness distributions, and decision
  rules.
- Checkpoint rule: 1-h checkpoints are retained as historical evidence but are
  not reused. New 0.5-h checkpoints are isolated by timestep and carry
  configuration, weather-input, source-code, seed, Git-commit, and file-integrity
  metadata.
- Additional numerical sensitivity: representative selected designs are
  evaluated at 0.25 h after the 0.5-h production rerun. This post-freeze check
  does not recursively change production resolution.

## 2026-09-24: supplementary JMA temporal resolution and acquisition route

- Old rule: acquire hourly JMA observations through the bulk-download table
  endpoint and use hourly forcing.
- New rule: retain immutable monthly daily-table HTML from JMA's Historical
  Weather Data Search and use daily mean temperature, precipitation, snowfall
  depth, and ground snow depth for supplementary station-winter scenarios.
- Reason: repeated production requests to the official bulk endpoint returned
  the site's menu HTML rather than a data file, after one exploratory response
  that was not persisted. Continued retries risked inappropriate request load.
  The public daily pages were stable, could be acquired sequentially at a
  respectful rate, and preserve the required station-winter coverage.
- Timing: no JMA scenario result had been viewed. Synthetic baseline, convergence,
  and uniform-front results had been viewed.
- Consequence: daily forcing cannot resolve subdaily shedding events and is
  reported only as supplementary scenario evaluation, not empirical validation.
- Regenerated outputs: processed JMA observation table, JMA station-winter
  evaluations, tables, figures, manuscript, supplement, audits, and package.

## 2026-09-24: uniform adhesion-grid implementation correction

- Old implementation: 30 slope levels and 30 friction levels were evaluated,
  with one of seven adhesion levels assigned deterministically to each pair.
- Corrected implementation: evaluate the full frozen Cartesian map of 30 slope,
  30 friction, and seven adhesion levels (6,300 uniform designs).
- Reason: assigning only one adhesion to each slope-friction pair did not provide
  a fair optimized uniform reference for heterogeneous designs that optimize
  adhesion independently.
- Timing: preliminary uniform outputs had been viewed; completed heterogeneous
  fronts and all comparative downstream analyses had not been viewed.
- Regenerated outputs: uniform design space and frontier, JMA comparison,
  sensitivity, robustness, tables, figures, manuscript, audits, and package.

## 2026-09-24: final-revision targeted secondary audits

- Frozen primary analysis preserved: `L_max`, `S_max`, the reduced-order model,
  production configuration, complete uniform map, and heterogeneous optimizer
  runs are unchanged.
- Added scope: common-normalization and reference-point sensitivity,
  cross-front knee comparability, matched-objective and constrained-threshold
  summaries, objective-equivalent robustness, constructability interpretation,
  and paired JMA trade-off summaries.
- Reason: these prespecified final-revision checks address reviewer-facing
  interpretation vulnerabilities without searching for favorable results.
- Reporting rule: all additions are secondary analyses and cannot be used to
  claim universal superiority or roof-scale validation.

## R1 major revision (post-review, 2026-11) — reviewer-driven methodological changes
All changes below were made after peer review of CRST-D-26-01129 and are distinguishable from the submitted analysis (tag `crst-submitted-v1`). Original outputs are preserved; revised outputs live in `results/r1/`.

6. **Transport and release model replaced** (`simulation_v2.py`): exact threshold-crossing release, Coulomb work–energy runout with inelastic entrainment, continuous routing for non-retaining cells. Reason: the submitted per-step transport made release mass a function of dt.
7. **Primary shedding endpoint replaced**: `S_event,max` (physical event mass; definition in `revision_r1/EVENT_METRIC_SPECIFICATION.md`), specified before any revised result. Submitted `S_max` retained as `legacy_s_step_max_kg_per_m` (diagnostic only).
8. **Forcing defined in continuous time** (`forcing_v2.py`); identical storms across dt.
9. **Constructability enforced inside optimisation** by feasible encoding (segments ≥ 3 cells, ≤ 6 transitions, integer slopes 2–45°, |Δslope| ≤ 12°, three discrete surface classes). Uniform reference evaluated exhaustively over the same constructable set (132 roofs); the 6,300-design continuous uniform map is re-run with the revised model as a sensitivity.
10. **Seeds increased** from 3 to 5 (1701, 2903, 4517, 6007, 8191); population 48 × 45 generations unchanged.
11. **Production dt = 1 h** selected by the pre-specified convergence rule (`revision_r1/NUMERICAL_CONVERGENCE_AUDIT.md`); nondominated designs re-checked at 0.0625 h and N = 48.
