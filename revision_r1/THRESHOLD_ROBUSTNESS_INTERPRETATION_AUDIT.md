# THRESHOLD_ROBUSTNESS_INTERPRETATION_AUDIT (R1 final pass)

Sources: `results/r1/review/uniform_threshold_check.csv`, `factor_rank_correlation_summary.csv`, `release_jump_drivers.csv`, `roof_length_sensitivity.csv` (`scripts/r1_review_analyses.py`).

## Former (40, 40) endpoint
- In the submitted analysis L_max = S_max = 40 kg m-1 for one uniform roof: the whole roof released at the moment its load reached the static threshold, so both objectives equal the threshold load c/[g(sin θ − μ_s cos θ)].
- Revised model: 60 of the 88 shedding constructable uniform roofs have L_max = S_event,max (whole-roof threshold release); the other 28 release in parts or as continuous streams. This is a model-threshold outcome, not a physical optimum; the manuscript (Section 3.2) and the response (R1-R2) say so.

## Current counts (8 m, dt = 1 h, base event definition)
- Uniform front: 26 unique pairs; uniform gap 91.9–6,417 kg m-1; 26 graded pairs inside it (S_event,max 11.5–91.8 kg m-1). Fine-resolution reconstruction gives the same count (NUMERICAL_EXCEPTION_IMPACT_AUDIT.md).

## Robustness interpretation
- Denominator of the "20%" figure: 17,000 draws = 68 nominal intermediate graded designs x 250 common uncertainty draws; 20.1% had S_event,max > 10x nominal (with a 1 kg m-1 floor on nominal).
- Draws with jumps: median friction multiplier 0.92 vs 1.00, adhesion 0.86 vs 1.01, snowfall 1.12 vs 0.93, temperature offset +0.26 vs −0.02 °C. Mechanism: the retaining segment of an intermediate design holds close to its failure threshold; weaker interfaces or more snow push it over the threshold, releasing the accumulated load in one event.
- Median Spearman ρ (intermediate designs, S_event,max): snowfall 0.54, adhesion −0.30, friction −0.13, temperature 0.16, density 0.04. Uniform shedding roofs: L_max vs adhesion 0.99 (threshold load ∝ c).
- Density has no material effect because it changes snow depth only and does not enter the failure criterion (Eq. 2, Eq. 4).
- These are properties of the synthetic perturbation model; no causal or population-level claim is made.

## Roof-length comparison fairness
- 4 m and 12 m: the same 317 designs (all 132 constructable uniform roofs + all 211 nondominated designs, deduplicated) were re-evaluated with 24 cells, the same constructability rules, the same event definition, dt = 1 h and the same three winters; each length uses its own re-evaluated uniform baseline. The 8 m run reproduces the base result exactly.
- Graded pairs in the uniform gap: 26 (4 m), 26 (8 m), 23 (12 m). No re-optimisation; counts are not transferred between lengths.

## Verdict
Explanations in the manuscript and response match the canonical outputs. No summary required recomputation.
