# ROBUSTNESS_AUDIT (R1)

Sources: `results/r1/robustness/{uncertainty_samples,robustness_runs,robustness_summary,robustness_classified,robustness_class_summary}.csv`; scripts `scripts/r1_robustness.py`, `scripts/r1_robustness_summary.py`.

## Design
All 211 designs on any nominal front (uniform, geometry, surface, joint, combined) x 250 common random draws (seed 7021) x 3 synthetic winters, dt = 1 h, revised event metric. Multipliers: lognormal friction, adhesion, fresh-snow density, snowfall; normal temperature offset (CVs/SD from `config/production.yaml`). Worst case over winters per draw; Q95 across draws. Max mass-balance error over 52,750 runs: 2.0e-11 kg/m.

## Findings
- Nominal intermediate graded designs (68 designs with L_max inside the uniform gap) had nominal S_event,max 0-92 kg/m, but Q95 S_event,max 0-4,340 kg/m (median 771). In a median 48% of draws their S_event,max exceeded 91.9 kg/m (the most retentive uniform shedding roof). Their small nominal releases are therefore not robust: they depend on a retaining segment holding near its threshold.
- Uniform shedding roofs were equally sensitive at the retentive end: the 20-degree smooth roof moved from nominal 91.9 to Q95 1,273 kg/m.
- In Q95 space the gap persists: uniform roofs give either Q95 L_max <= 145 kg/m or full retention (8,472 kg/m); 24 graded designs form the Q95 front between 1,149 and 7,416 kg/m, with Q95 S_event,max 162-1,037 kg/m, i.e. below every uniform shedding roof (>= 1,273 kg/m).
- Interpretation: grading supplies intermediate options under uncertainty, but the release masses of those options are an order of magnitude larger at Q95 than nominally. The manuscript reports both; no claim of robust small releases is made.

## Limitations
Uncertainty is parametric only (no structural model uncertainty, no correlated spatial variability along the roof, no product-specific friction distributions). CVs are assumptions (see PHYSICAL_PARAMETER_PROVENANCE.csv).
