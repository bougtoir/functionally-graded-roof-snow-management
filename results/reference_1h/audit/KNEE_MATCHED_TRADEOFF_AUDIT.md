# Knee and matched-trade-off audit

## Knee selection

The original knee procedure minimizes Euclidean distance to the ideal after
normalizing each front by its own minimum and maximum. This is valid as a
within-front descriptive selection, but it does not provide a common
scalarization for comparing different fronts.

Under front-specific normalization, the selected joint point is
`3210.636/39.9995 kg m-1`. Under common normalization using the combined
observed objective bounds, the selected joint point is
`2941.908/43.3328 kg m-1`. The change demonstrates that the selected “knee” is
normalization-dependent. The original `+3913.3%/-50.0%` contrast is therefore
not suitable as a headline comparison.

## Matched constraints

The complete stepwise comparison evaluates every unique observed `L_max` and
`S_max` threshold. At matched retained-mass caps, the six intermediate joint
pairs reduce `S_max` relative to the uniform set. At matched release-mass caps
below 80 kg m-1, the same points reduce `L_max` relative to the uniform
retention endpoint.

The three release limits already frozen for decision analysis are also reported
separately:

- at 20 kg m-1, joint grading reaches a lower retained mass than the uniform
  retention endpoint;
- at 80 and 200 kg m-1, the uniform and joint sets both include the
  `79.999/79.999 kg m-1` shedding regime.

No new threshold was selected after viewing results.

## Unique objective-space regions

Six intermediate joint objective pairs are not attainable by the optimized
uniform set under simultaneous equal-or-tighter `L_max` and `S_max` caps. This
is the strongest supported primary comparative result. It is conditional on
the reduced-order model, sampled design spaces, and approximate heterogeneous
search.

## Gate

Status: PASS. Final reporting must lead with matched constraints and unique
regions, label both knee methods, and remove the large front-specific knee
percentage from the abstract.
