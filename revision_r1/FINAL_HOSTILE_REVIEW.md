# FINAL_HOSTILE_REVIEW (R1)

Extends HOSTILE_REVIEW_FINAL.md with the final-pass findings.
- R2 #1/#4: convergence is aggregate (29 of 543 pairs fail a metric at dt = 1 h). None is a graded gap design; fine-resolution fronts give the same 26 gap pairs. Stated in Sections 2.4 and 3.1. Not a proof that every design converged.
- R2 #3 / R1 general: parameters are literature-informed assumptions, not validated; status PARTIALLY ADDRESSED. No roof-scale validation exists.
- R2 #6: constraints inside NSGA-II; 100% feasible.
- R2 #7: hypervolume difference small (0.982 vs 0.988); no superiority claim; graded fronts are lower bounds.
- Threshold artefacts: (40,40) explained as whole-roof threshold release; intermediate releases are threshold-sensitive (20.1% of 17,000 draws > 10x nominal).
- Per-run claim holds at dt = 1 h (15/15); at fine resolution only pooled-front designs were rechecked (9/15 runs contributed to the 26 fine gap pairs) - documented in NUMERICAL_EXCEPTION_IMPACT_AUDIT.md.
Decision: CONDITIONAL READY / READY FOR AUTHOR ACTIONS - no critical numerical or scientific problem undermines the main constrained claim; remaining limitations are explicit.
