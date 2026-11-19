# NUMERICAL_EXCEPTION_IMPACT_AUDIT (R1 final pass)

Source: `scripts/r1_exception_audit.py` -> `results/r1/review/exception_failed_cases.csv`, `exception_summary.json`, `exception_fine_gap_per_run.csv`.

## Denominator and criterion
- Unit of comparison: unique design-winter pairs (543 = 181 designs x 3 synthetic winters; 132 constructable uniform roofs + 49 unique random constructable graded roofs after duplicate removal), dt = 1 h vs the dt = 0.0625 h reference, both with 24 cells.
- Tolerance per pair and metric: |X_dt - X_ref| <= max(0.02 |X_ref|, 1 kg m-1). A timestep is acceptable if >= 95% of pairs meet the tolerance for every metric, >= 90% have event counts within one, and mass-balance error < 1e-6 kg m-1.
- "All steps passed" means every tested timestep met this aggregate rule. It does NOT mean every pair converged.

## Exceptions at dt = 1 h
- 29 of 543 pairs fail at least one metric (S_event,max 22, S_1h 16, L_max 10, total release 7); 13 uniform, 16 graded.
- Largest: uniform 24x28d2 (rough retention class, 28 degrees), severe inland winter, L_max = S_event,max = 6,232 vs 4,900 kg m-1 (|diff| 1,333). Static friction alone holds this roof (tan 28 < mu_s), so it fails only while the near-melt friction reduction lowers mu below tan theta; the length of that sub-threshold window is resolved differently at 1 h and 0.0625 h. This is a temporal-resolution effect on a genuine model threshold, not a mass-balance or event-segmentation defect (mass balance 0; event count unchanged).
- Several other failures change the event count by one (split/merge of closely spaced releases).

## Mapping onto the reported results
- (a) uniform front: 7 failing uniform designs lie on the dt = 1 h uniform front; (b,c) combined front: 1 failing design; graded designs inside the uniform gap: 0.
- (d,e) Re-evaluating all 211 nondominated designs at dt = 0.0625 h (and 48 cells) changed hypervolume to 0.9822 (uniform) and 0.9880 (joint); ordering unchanged.
- Fine-resolution reconstruction (uniform objectives from the dt = 0.0625 h convergence runs, graded objectives from the fine re-check): uniform front 26 pairs, gap 91.8-6,417 kg m-1, 26 graded pairs inside it, S_event,max 11.5-91.8 kg m-1 - identical in count to dt = 1 h.
- (f) Per-seed: at dt = 1 h every one of the 15 runs found gap pairs on its own front (8-23). At fine resolution only the pooled-front designs were re-evaluated; 9 of 15 runs contributed designs to the 26 fine-resolution gap pairs (0-9 per run). The per-run claim is therefore a dt = 1 h result, and the manuscript states it as such.

## Verdict
The exceptions are concentrated in threshold-boundary uniform and random graded designs that are not intermediate gap designs; the existence and count of graded intermediate pairs and the direction of all front comparisons are unchanged at fine resolution. Central constrained result: STABLE. Numerical convergence is aggregate, not universal, and is distinct from physical validation (none performed).
