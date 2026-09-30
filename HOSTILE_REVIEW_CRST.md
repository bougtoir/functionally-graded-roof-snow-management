# Hostile pre-submission review for CRST

Review stance: the manuscript was evaluated as if by three skeptical reviewers:
a snow/cold-regions physicist, a numerical multiobjective-optimization
specialist, and a roof-engineering practitioner. The review distinguishes
frozen primary analyses from justified corrective secondary analyses.

## Submission-blocking findings

### H01. The abstract foregrounds a non-comparable cross-front knee contrast

- Perspective: numerical optimization
- Severity: critical
- Evidence: the uniform and joint knees are each selected after separate
  front-specific min-max normalization. The reported comparison of
  `79.999/79.999` with `3210.636/39.9995 kg m-1` therefore compares two
  different scalarizations. The resulting `+3913.3%` retained mass is likely to
  be read as a penalty or benefit even though the selection rules are not
  cross-front comparable.
- Required action: remove this contrast from the abstract and headline result;
  retain it only as a labeled illustration, if at all. Add common-normalization,
  matched-objective, and constrained-threshold comparisons.
- Reanalysis needed: yes.
- Final status: open for Phases 04 and 09-10.

### H02. Reported Pareto counts are predominantly objective duplicates

- Perspective: numerical optimization
- Severity: critical
- Evidence: the current files contain 2,912/320/1,731/1,928 nondominated design
  rows for uniform/geometry/surface/joint but only 2/15/2/8 unique
  `L_max`-`S_max` pairs. Distinct profiles may legitimately share an objective
  pair, but calling all rows Pareto “points” visually and textually exaggerates
  objective-space resolution.
- Required action: report both nondominated design rows and unique objective
  pairs; calculate frontier indicators on deduplicated objective pairs and
  explain why design duplicates are retained separately.
- Reanalysis needed: yes.
- Final status: open for Phases 03 and 09.

### H03. The production timestep does not pass the frozen four-metric criterion

- Perspective: snow physics and numerics
- Severity: critical
- Evidence: the `N=24`, `dt=1 h` production case is marked
  `within_tolerance=False`; its SSCI relative error is 9.38% against the
  `dt=0.5 h` reference, exceeding the frozen 8% tolerance. For the selected
  joint knee, the sensitivity table changes `S_max` from 39.9995 at 1 h to
  79.7529 at 2 h and 21.6603 at 0.5 h. `S_max` is explicitly mass per timestep,
  so changing the interval changes the estimand as well as numerical behavior.
- Required action: state that the production timestep failed the composite
  convergence gate; do not imply general convergence. Add a selected-design
  timestep audit and distinguish interval release mass from a
  timestep-invariant release rate or physical event.
- Reanalysis needed: yes.
- Final status: open for Phases 03-04 and 09-10.

### H04. The primary joint optimum is not constructability-constrained

- Perspective: roof engineering
- Severity: critical
- Evidence: optimization enforces only the adjacent-slope constraint. The
  selected continuous joint knee has 23 combined transitions and a
  one-cell minimum segment, violating the configured maximum of 6 transitions
  and minimum of 3 cells. Those constraints are applied only in post hoc
  mapping. The manuscript wording can be read as if they constrained the
  optimized frontier.
- Required action: distinguish unconstrained continuous optimization from
  post hoc manufacturable mapping. Give constrained/mapped results equal
  prominence and treat the complexity-penalty selection of the uniform
  `80/80` design as a substantive negative result. Run a constrained
  optimization only if the post hoc screen cannot answer the objection.
- Reanalysis needed: targeted screen first; optimization only if justified.
- Final status: open for Phases 06 and 09-10.

### H05. The claimed robust selection is not uniquely supported

- Perspective: numerical optimization
- Severity: critical
- Evidence: several nominally `79.999/79.999` designs have identical reported
  Q95 outcomes and identical rounded robust-selection scores. Selection of
  `joint_02` is made by `idxmin()`, so row order can break a tie. A uniform
  candidate also has `103.786/103.786` Q95 values. The statement that the robust
  selection “was joint_02” overstates uniqueness.
- Required action: report the tied or practically equivalent robust set,
  define numerical tie tolerance, and compare objective-equivalent designs by
  their full perturbation distributions and design attributes.
- Reanalysis needed: yes.
- Final status: open for Phases 05 and 09-10.

## High-priority major-revision findings

### H06. Hypervolume and epsilon are underdefined and easily overinterpreted

- Perspective: numerical optimization
- Severity: high
- Evidence: “normalized hypervolume” divides objectives by a common raw
  reference equal to 1.05 times the largest observed objective, with an implicit
  zero ideal. Epsilon uses a different common min-span normalization.
  Sensitivity to defensible common bounds/reference points is not shown.
- Required action: document ideal, nadir, normalization, reference point, and
  objective direction; repeat metrics under prespecified common alternatives.
  Explain that joint hypervolume can exceed uniform while epsilon versus
  uniform is zero because the joint set can match uniform at required regions
  while occupying additional unique trade-off regions.
- Reanalysis needed: yes.
- Final status: open for Phases 03 and 09.

### H07. “Complete” overstates heuristic heterogeneous optimization

- Perspective: numerical optimization
- Severity: high
- Evidence: the uniform space is exhaustively evaluated at 6,300 combinations,
  whereas heterogeneous fronts are heuristic accumulations from three
  48-by-45 NSGA-II runs. Per-seed joint hypervolume varies from 0.268 to 0.336
  under its seed-analysis reference, and per-seed epsilon versus the combined
  set remains about 0.21-0.25.
- Required action: call the heterogeneous results observed or approximate
  nondominated sets, not complete attainable fronts. Report seed variability
  prominently and avoid using pooled histories as evidence of global
  convergence.
- Reanalysis needed: no new optimization required; metrics audit required.
- Final status: open for Phases 03 and 10.

### H08. Numerical convergence is tested on one uniform regression design only

- Perspective: snow physics and numerics
- Severity: high
- Evidence: the 3-by-3 convergence table evaluates the uniform intermediate
  design. It does not test discontinuous heterogeneous transport patterns,
  mapped profiles, or the robust candidate.
- Required action: add scoped resolution/timestep checks for representative
  selected designs and state that these do not prove frontier-wide convergence.
- Reanalysis needed: yes, targeted evaluations only.
- Final status: open for Phase 09.

### H09. The robustness design is a scenario perturbation, not empirical uncertainty

- Perspective: snow physics
- Severity: high
- Evidence: five perturbations are sampled independently; single multiplicative
  factors are applied globally across cells and weather scenarios. Ranges are
  assumed coefficients of variation, not fitted distributions. Fresh-snow
  density does not alter synthetic mass-based primary objectives at fixed mass.
- Required action: state independence and perfect spatial/scenario correlation
  assumptions, justify ranges as scenario bounds, and avoid confidence-interval
  language. Separate parameters that affect primary objectives from those that
  affect depth diagnostics.
- Reanalysis needed: audit and stratified summaries; no fishing.
- Final status: open for Phases 05 and 10.

### H10. Aggregate robustness medians mix unlike candidate designs

- Perspective: numerical optimization
- Severity: high
- Evidence: manuscript medians are computed over every draw and every selected
  candidate within a design class. This mixture depends on candidate sampling
  density and obscures candidate-level fragility.
- Required action: replace class-pooled medians with candidate-level Q95,
  intervention probability, and explicit comparisons among nominally
  objective-equivalent designs.
- Reanalysis needed: yes.
- Final status: open for Phases 05 and 10.

### H11. Model simplifications create exploitable threshold behavior

- Perspective: snow physics
- Severity: high
- Evidence: release is triggered by a cellwise static force threshold, followed
  by same-step one-dimensional transport capped by a transport fraction. The
  model omits fracture, slab continuity, wind redistribution, roof details,
  and three-dimensional paths. Numerous designs collapse to exactly the same
  objective pairs, consistent with broad threshold regimes.
- Required action: discuss optimizer exploitation explicitly; interpret unique
  threshold regimes rather than fine design ranking. Avoid material-specific
  prescriptions.
- Reanalysis needed: no; interpretation and duplicate audit required.
- Final status: open for Phases 03 and 10.

### H12. JMA results show a consistent trade-off, not validation or superiority

- Perspective: snow physics and roof engineering
- Severity: high
- Evidence: in all 12 station-winters, the joint knee lowers `S_max` but raises
  `L_max`, often by several-fold. Daily ground observations cannot resolve
  hourly eave-release events and are converted using an assumed fresh-snow
  density.
- Required action: add paired ratios/differences without significance tests,
  use station names, and frame the finding as lower interval release mass
  purchased with higher retained modeled mass.
- Reanalysis needed: yes.
- Final status: open for Phases 07 and 09-10.

### H13. Parameter provenance does not support predictive roof design

- Perspective: snow physics and roof engineering
- Severity: high
- Evidence: friction, adhesion, compaction, melt, aging, kinetic ratio, and
  intervention thresholds include explicit uncalibrated assumptions or broad
  generic ranges. Literature supports directions and mechanisms, not the
  configured numerical parameter set.
- Required action: separate evidence-supported mechanism choices from assumed
  magnitudes and make calibration status prominent in Methods, Discussion, and
  cover letter.
- Reanalysis needed: no.
- Final status: open for Phases 02, 08, and 10.

### H14. Retention and non-shedding roofs receive insufficiently balanced treatment

- Perspective: roof engineering
- Severity: high
- Evidence: the manuscript lists Japanese strategy categories but does not
  adequately explain that retention can be intentionally preferred where
  shedding exposure is unacceptable, provided structure, drainage, cornices,
  and maintenance are addressed.
- Required action: strengthen the literature-supported rationale for retention,
  shedding, melting, and hybrid strategies; explicitly state that this study
  does not invalidate non-shedding roofs.
- Reanalysis needed: literature verification only.
- Final status: open for Phase 08 and 10.

## Medium-priority findings

### H15. Table 3 loss columns are ambiguous

- Perspective: roof engineering
- Severity: medium
- Evidence: `l_max_discretization_loss` and `s_max_discretization_loss` are
  absolute differences in `kg m-1`, but captions do not identify absolute
  versus percentage loss.
- Required action: rename columns and add percentage changes or an explicit
  units note.
- Reanalysis needed: arithmetic only.
- Final status: open for Phases 06 and 11.

### H16. Figure 3 likely hides the decision-relevant low-mass region

- Perspective: all
- Severity: medium
- Evidence: fronts span roughly 80-6417 `kg m-1`, while several unique release
  regimes cluster near the low end. Full-range linear axes can make the apparent
  gain depend on a few staircase points.
- Required action: preserve a full-range panel and add a clearly labeled inset
  or transformed panel if it improves resolution. Plot unique objective pairs
  separately from design multiplicity.
- Reanalysis needed: no new simulation.
- Final status: open for Phase 11.

### H17. Novelty is methodological and must be stated narrowly

- Perspective: CRST editor
- Severity: medium
- Evidence: slope, friction, retention, and shedding are established topics.
  The defensible contribution is reproducible comparison of exhaustive uniform
  and approximate spatially graded trade-off sets under common forcing, with
  robustness and constructability audits.
- Required action: sharpen the Introduction, cover letter, and scope-fit
  statement around that contribution without claiming a validated roof system.
- Reanalysis needed: no.
- Final status: open for Phases 10 and 16.

### H18. References are incomplete as journal citations

- Perspective: CRST editor
- Severity: medium
- Evidence: generated references omit volume, issue, and pages even when these
  are available; one author string produces “et al..”. Official Japanese
  sources require verified titles, dates, URLs, and regional transfer limits.
- Required action: verify every record and generate complete Vancouver-style
  references in order of appearance.
- Reanalysis needed: literature metadata audit.
- Final status: open for Phases 08 and 12-13.

## Overall verdict

Current recommendation: **major revision; do not submit the current package**.
The study can become submission-ready without restarting the model if the
revision centers the optimized uniform reference, unique objective regimes,
timestep dependence, robustness non-uniqueness, and constructability. The
most defensible prospective conclusion is conditional: spatial grading expands
parts of the modeled trade-off set, while robustness and constructability can
substantially alter or eliminate nominal advantages.
