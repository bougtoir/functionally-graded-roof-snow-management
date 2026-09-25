# Final hostile review

Status: PASS

## Desk-rejection risks

| Risk | Final assessment |
|---|---|
| Journal scope | Addressed: reduced-order cold-regions roof-snow design-space study; no structural-validation claim. |
| Comparator fairness | Addressed: exhaustive 6,300-design uniform grid precedes heuristic heterogeneous comparison. |
| Numerical resolution | Addressed: 0.5 h is the production reference; failed 1-h comparison and targeted 0.25-h sensitivity are disclosed. |
| Constructability | Addressed: no continuous joint row passed all checks; mapped profile is not called a constrained optimum. |
| Robustness | Addressed: nominally equivalent designs differ and the minimum score has a 6-way tie. |
| JMA interpretation | Addressed: daily ground observations are scenario forcing, not roof-scale validation. |

## High-risk numerical claims

- Uniform unique objective pairs: 2.
- Joint unique objective pairs: 6; nominal additional intermediate pairs: 4.
- Joint rows passing every post hoc constructability check: 0.
- Selected-knee mapping changes: Lmax -98.28%, Smax +537.47%.
- Failed selected-design comparisons: 3/3 at 1 h versus 0.5 h and 3/3 at 0.5 h versus the targeted 0.25-h reference.

## Verdict

The nominal joint front retains intermediate modeled trade-offs, but the central practical interpretation is negative: constructability and interval sensitivity dominate the theoretical grading benefit. This conclusion does not rely on JMA validation, structural safety, or universal-superiority claims.

## Reproducibility and residual items

- Fresh reproduction: PASS (CHECKPOINT-BASED). All canonical 0.5-h checkpoint manifests passed configuration, source, weather, seed, and checksum compatibility checks. Figures, Tables, manuscript files, and the submission package were regenerated and validated from those outputs; no detached full optimizer rerun is claimed.
- Author affiliation, postal address, funding, competing interests, CRediT roles, originality, and final AI-responsibility wording remain for local completion.
