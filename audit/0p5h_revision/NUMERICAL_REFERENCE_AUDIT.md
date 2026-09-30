# Post-freeze 0.25-hour numerical sensitivity

The 0.5-h production designs were reevaluated at 0.25 h using the same forcing totals and unchanged outcome definitions. This is a targeted sensitivity check, not a second optimizer run and not a rule for recursively changing production resolution.

| Design | L_max error | S_max error | Event-count error | SSCI error |
|---|---:|---:|---:|---:|
| uniform_knee | 99.973% | 99.973% | 46.543% | 99.667% |
| joint_continuous_knee | 0.002% | 85.337% | 44.111% | 91.450% |
| joint_mapped_knee | 27.027% | 27.277% | 10.672% | 11.798% |

`S_max` is interval-specific by definition. The 0.25-h result therefore constrains interpretation but does not redefine the frozen primary outcome or trigger a whole-optimizer rerun.
