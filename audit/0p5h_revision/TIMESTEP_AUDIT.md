# Timestep root-cause audit

## Design and definitions

The 1-h selected uniform, continuous-joint, and mapped-joint designs were reevaluated at 1.0 and 0.5 h using weather resampled from the same 0.5-h master series. `L_max`, `S_max`, event count, and SSCI definitions were not changed. `S_max` remains the maximum mass released in one simulation interval and is therefore inseparable from its timestep.

## Diagnostics

- Maximum forcing-total difference: 0 kg m-1.
- Maximum relative change in total shed mass: 0.315%.
- Maximum absolute relative change in `S_max`: 49.974%.
- Maximum absolute relative change in mean event count: 90.782%.
- Maximum absolute mass-balance error: 3.63798e-12 kg m-1.

## Root cause

The identical forcing totals and substantially larger change in `S_max` than in total shed mass identify within-step aggregation and threshold-event partitioning as the main cause. Snowfall/melt timing and transport discretization contribute to the remaining retained-mass and SSCI differences.

The failure is not repaired by redefining events or outcomes. It justifies rerunning production at the frozen 0.5-h reference resolution and continuing to report `S_max` with its interval.
