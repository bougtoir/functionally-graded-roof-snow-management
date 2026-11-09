# HOSTILE_REVIEW_FINAL (R1)

Critical pre-submission review of the R1 clean manuscript, written from a sceptical reviewer's position. Each item states the attack, the evidence, and the action taken.

| # | Attack | Evidence | Action / residual risk |
|---|---|---|---|
| 1 | "The model is not validated; all results are artefacts of assumed friction/adhesion." | No roof-scale release data; parameters are assumptions (PHYSICAL_PARAMETER_PROVENANCE.csv). | Stated in abstract, 4.1 and conclusions; "verified numerically, not validated". Residual: high; inherent to the study. |
| 2 | "The new metric was chosen to make graded roofs look good." | Metric specified before revised production runs (EVENT_METRIC_SPECIFICATION.md); legacy per-step value still reported; separation-time sensitivity in Table 3. | 3.5 and 4.1 state that shedding-roof release magnitudes depend on the separation time. Gap existence held for every variant (4-26 graded pairs). |
| 3 | "dt = 1 h is too coarse." | Prespecified criterion met; boundary designs differ up to 1,333 kg/m; all front designs re-run at 0.0625 h / 48 cells (S p95 change 5.9 %, max 13.4 %; HV unchanged to 3 d.p.). | Reported in 3.1 and 3.4. |
| 4 | "Graded roofs are not better; hypervolume gain is trivial." | HV 0.982 -> 0.988; matched median gain about 0.5 %. | Manuscript makes no superiority claim; gain described as small. |
| 5 | "The 26 gap pairs is a post hoc statistic." | Defined after fronts were seen. | Methods 2.6 labels it descriptive; found in all 15 runs. |
| 6 | "Small releases of intermediate designs are fragile." | Q95 S_event,max median 771, max 4,340 kg/m vs nominal <= 92. | Abstract, 3.6, Discussion and Conclusions state this explicitly. |
| 7 | "Q95 'front' mixes marginal quantiles." | Q95 taken per objective. | Methods 2.7 now states it is not a joint design point. |
| 8 | "Uniform roofs could fill the gap with other surfaces." | Continuous uniform grid of 6,300 designs (slope, friction, adhesion) still leaves a gap from 83.7 to 6,417 kg/m. | Reported in 3.2. |
| 9 | "Constructability was cosmetic." | Constraints enforced in the decoder; 100 % feasible; random probes 20,000/20,000. | Methods 2.5. Residual: no cost, fastening or waterproofing model. |
| 10 | "JMA data are presented as validation." | Daily totals spread over 24 h; no roof observations. | Methods 2.3 and 3.7 state scenario forcing only. |
| 11 | "Rain-on-snow / hydrology ignored." | No liquid retention, refreezing, drainage, hydrological triggering. | Listed in 4.1 as unrepresented. |
| 12 | "Japanese regulatory claims overreach." | Article 86 and heavy-snowfall statistics verified from official raw snapshots. | Text states no compliance claim and that retaining roofs carry full design load. |
| 13 | "Optimiser may not have converged." | Per-seed HV changes 30->45 generations <= 0.0005; heuristic. | Reported (Fig. 6); no global-optimality claim. |
| 14 | "Single-author, AI-assisted work." | Generative-AI declaration included. | Author must confirm CRediT, funding, competing interests and affiliation (open REQUIRED fields). |

Unresolved before submission: reviewer comments not supplied (no point-by-point response possible); author metadata placeholders; identity of the archived baseline with the Editorial Manager file unconfirmed.
