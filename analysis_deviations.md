# Analysis deviations

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
