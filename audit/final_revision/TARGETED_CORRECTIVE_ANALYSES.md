# Targeted corrective analyses

## Scope

Only analyses justified by the hostile-review findings were added:

1. common-normalization and front-specific knee comparison;
2. matched-`L_max`, matched-`S_max`, and prespecified-threshold comparisons;
3. common reference-point sensitivity for frontier metrics;
4. robustness within nominally objective-equivalent candidates;
5. direct constructability feasibility and continuous-to-discrete loss;
6. paired JMA station-winter ratios and differences;
7. selected-design timestep sensitivity.

No new optimizer search was run, and no model parameter was changed to improve
heterogeneous outcomes.

## Selected-design timestep audit

The uniform knee, continuous joint knee, and mapped joint knee were evaluated
at 2.0, 1.0, and 0.5 h using weather resampled from the same 0.5 h master
series. Relative errors use the 0.5 h result for the same design as reference
and retain the frozen four-metric 8% criterion.

The production 1 h timestep remains a known numerical limitation wherever the
four-metric criterion fails. Results must not be described as timestep
converged merely because one objective is stable. The 0.5 h results are a
sensitivity reference, not a replacement optimized frontier: the designs were
optimized at 1 h and were not reoptimized at 0.5 h.

All three selected designs fail the composite criterion at 1 h. The maximum
relative errors are 99.90% for the uniform knee, 98.60% for the continuous
joint knee, and 46.17% for the mapped joint knee. For the continuous joint
knee, `L_max` changes by only 0.03%, but `S_max`, event count, and SSCI remain
timestep sensitive. The uniform `S_max` approximately scales with interval
length because it is defined as mass released in one timestep. This confirms
that `S_max` must always be reported with its interval and that numerical
convergence cannot be claimed for the production setting.

## Interpretation

- Knee conclusions depend on normalization and are not valid headline
  superiority percentages.
- Joint hypervolume gain identifies additional intermediate trade-offs, not
  front-wide dominance.
- Nominal objective equality does not imply robustness equality.
- The mapped design is a feasible translation, not a constrained optimum.
- JMA results are paired modeled scenarios, not empirical roof validation.

## Gate

Status: PASS with the unresolved timestep limitation carried into the abstract,
results, discussion, limitations, and final audit.
