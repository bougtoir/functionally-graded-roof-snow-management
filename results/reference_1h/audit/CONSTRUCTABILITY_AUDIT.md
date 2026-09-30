# Complexity and constructability audit

## Constraint timing

The continuous heterogeneous optimizer enforces the maximum adjacent slope
change. It does not enforce the configured minimum segment length, maximum
transition count, or discrete generic surface classes. Those requirements are
applied by a post hoc manufacturable-mapping routine.

The final Methods and Figure 4 must not describe all four rules as optimizer
constraints.

## Continuous fronts

All uniform rows satisfy the three numerical constructability checks. Most
surface-only rows satisfy them, but the retention objective pair does not.
No geometry-only row satisfies all checks.

Only 9 of 1,928 joint rows satisfy all checks, and all nine belong to the
`79.999/79.999 kg m-1` objective pair. None of the six intermediate joint
trade-off pairs is directly feasible under all continuous-profile checks.
This is a substantive limitation of the nominal heterogeneous frontier.

## Post hoc mapping

The generic-class mapping reduces the selected joint profile from 23 to 6
slope transitions and from 23 to 3 surface transitions. Relative to the
continuous front-specific knee:

- `L_max` increases by 11.678 kg m-1 (0.364%);
- `S_max` increases by 4.412 kg m-1 (11.030%).

The existing Table 3 “loss” fields are absolute changes in `kg m-1`, not
percentages. Revised output must label both absolute and percentage changes.
The mapped point remains a heuristic feasible translation, not a
constructability-constrained optimum.

## Complexity penalty

At all frozen transition penalties (0, 0.1, and 0.25), the selected design is
the uniform `79.999/79.999 kg m-1` regime. This negative result must be
prominent: even a zero explicit transition penalty selects uniform under the
current equal-weight normalized objective score, and positive penalties do not
change that selection.

## Decision on new optimization

A new constrained optimization is not required for this revision. The
post hoc mapped profile demonstrates the performance loss of one transparent
feasible translation, while the full continuous-front feasibility audit shows
that nominal intermediate advantages do not survive direct constraint
screening. Running a new search solely to recover favorable heterogeneous
points would violate the no-rescue rule.

## Gate

Status: PASS with a required limitation and table-label correction.
