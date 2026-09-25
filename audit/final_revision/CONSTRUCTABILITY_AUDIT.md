# Constructability audit

Frozen adjacent-slope, minimum-segment, transition-count, rounding, surface-class, and penalty rules were not loosened.

| Class | Design rows | Feasible rows |
|---|---:|---:|
| uniform | 2910 | 2910 |
| geometry | 155 | 0 |
| surface | 270 | 254 |
| joint | 1341 | 0 |

No continuous joint row passed every check. Mapping the joint knee reduced slope transitions from 23 to 6 and surface transitions from 23 to 0. It changed Lmax by -4469.094 kg m-1 (-98.279%) and Smax by +66.000 kg m-1 (+537.469%). The mapped profile is a post hoc feasible translation, not a constrained optimum.
