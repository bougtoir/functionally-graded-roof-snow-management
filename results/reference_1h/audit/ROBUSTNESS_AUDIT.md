# Robustness audit

## Design

The robustness stage uses 250 deterministic common-random-number draws for each
of 25 selected candidates. Each sample applies the same friction, adhesion,
fresh-snow-density, snowfall, and temperature perturbation to every candidate,
which supports paired candidate comparisons. The perturbations are independent
scenario factors; they are not fitted empirical distributions and the reported
95th percentiles are not confidence intervals.

The selected candidates are 12 row-spaced designs plus a knee when it is not
already selected. Because fronts contain many objective duplicates, this rule
samples design degeneracy rather than balancing unique objective pairs. The
robustness analysis therefore characterizes the retained candidate set, not
the complete design space.

## Objective-equivalent but robustness-distinct designs

Fourteen candidates have the same nominal `79.999/79.999 kg m-1` objective
pair. Their Q95 `L_max`, Q95 `S_max`, and intervention probability span:

- Q95 `L_max`: 103.786 to 7465.520 kg m-1;
- Q95 `S_max`: 103.786 to 5482.601 kg m-1;
- intervention probability: 0 to 0.432.

Thus nominal objective equality does not imply perturbation equivalence. This
is a supported secondary finding and is more informative than class-pooled
draw medians.

The nominal joint knee has Q95 values of approximately
`4200.414/226.043 kg m-1` and intervention probability 1.0. It is not the
robust selection.

## Robust selection

Six candidates share the exact minimum scalarized robust score within
`1e-12`: five joint labels and one uniform label. They also share the reported
Q95 `103.786/103.786 kg m-1` and zero intervention probability. The existing
single flag on `joint_02` is a row-order tie break, not a unique scientific
selection.

The final manuscript must report the six-candidate tie set or select among it
using a prospectively justified secondary criterion. It must not state that
`joint_02` is uniquely robust.

## Dependence and parameter interpretation

One perturbation factor is shared globally across cells and scenarios within a
draw. Factors are independent of each other. Density affects depth and
depth-based diagnostics but not mass-based snowfall forcing when snowfall mass
is held fixed. These assumptions must be explicit.

## Gate

Status: PASS with corrected interpretation. No Monte Carlo rerun is required;
the retained draw-level file is sufficient for the tie-aware and
objective-equivalent analyses.
