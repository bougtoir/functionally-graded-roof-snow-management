# SEMANTIC_CODE_AUDIT (R1)

| # | Location (submitted code) | Finding | Consequence | R1 resolution |
|---|---|---|---|---|
| 1 | `simulation.py` transport | Travel per step `0.5·a·dt²` from rest; with dt = 1800 s the moved fraction is always 1 | Whole cell content moves exactly one cell per step: transport speed = Δx/dt, a numerical artefact | `simulation_v2.py`: Coulomb work–energy runout, dt-free |
| 2 | `simulation.py` ridge→eave sweep | Mass received by cell i+1 is re-tested in the same step (Gauss–Seidel) | Order-dependent cascade length per step | Explicit runout with entrainment; releases processed in physical time |
| 3 | `simulation.py` events | "Events" = timesteps with outflow ≥ 0.1 kg m⁻¹; `S_max` = largest step | Event mass ∝ dt for continuous outflow (40→20 kg m⁻¹) | Physical events (`segment_events`) and window maxima |
| 4 | `simulation.py` failure check | Failure tested at step end after full-step loading | Overshoot of threshold by up to one step of snowfall | Exact crossing time within step |
| 5 | `weather.py` | Forcing sampled at step start | Different dt see different storms | `forcing_v2.py`: exact integrals / 15-s aggregation |
| 6 | `optimization.py` | Only adjacent-slope constraint inside NSGA-II; segments and classes applied post hoc | Reported frontiers were not constructable | `optimization_v2.py` feasible encoding (100 % constructable) |
| 7 | `study.evaluate_design` | Worst case over winters taken separately for L and S | Objectives may come from different winters | Retained (conservative envelope) and documented; per-winter values stored |
| 8 | Units | Masses per cell divided by width 1 m → kg m⁻¹ of roof strip | Consistent | Unchanged |
| 9 | Signs / denominators | SSCI over per-step values | Step-dependent | Event-level SSCI |
| 10 | Kinetic-energy proxy | Sum of positive specific energy over all cells, not trajectory | Not a physical exit energy | Exit kinetic energy ½ M v² from runout |

Tests: `tests/test_simulation_v2.py` (analytic threshold mass, mass conservation, dt independence, event merging, encoding feasibility).
