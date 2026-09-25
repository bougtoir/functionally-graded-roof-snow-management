# Numerical consistency audit

Overall status: PASS

- Canonical production timestep: 0.5 h.
- Selected designs failing the 1-h versus 0.5-h four-metric criterion: 3/3.
- The 0.5-h results are the production reference, not evidence of convergence at finer intervals.
- Selected 0.5-h designs failing the targeted 0.25-h sensitivity criterion: 3/3.
- Lmax and Smax definitions were unchanged. Smax remains an interval release mass and is reported with its timestep.
- Maximum absolute mass-balance error in the 1-h/0.5-h root-cause audit: 3.638e-12 kg m-1.
- The 0.25-h check is a post-freeze sensitivity and did not trigger another production-resolution change.
