# Phase 05 handoff: robustness

Status: PASS

## Findings

- Every candidate has 250 draws and all candidates share the same perturbation
  factors within each draw.
- Fourteen nominal `79.999/79.999` candidates have Q95 outcomes ranging from
  `103.786/103.786` to `7465.520/5482.601 kg m-1`.
- Six candidates tie for the minimum robust score, including five joint and one
  uniform design.
- The prior single `joint_02` flag is row-order tie breaking.
- The nominal joint knee has Q95 `4200.414/226.043 kg m-1` and intervention
  probability 1.0.

## Evidence

- `audit/final_revision/ROBUSTNESS_AUDIT.md`
- `results/generated/final_revision_robustness_candidate_audit.csv`
- `results/generated/final_revision_objective_equivalent_robustness.csv`
- `results/generated/final_revision_robust_selection_ties.csv`
