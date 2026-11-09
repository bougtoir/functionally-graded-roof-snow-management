# Internal working notes for CRST-D-26-01129 R1 (not a deliverable)

Branch: devin/1794200841-crst-major-revision (from main 472807b). Master prompt: user attachment (CRST major revision).
Reviewer comment ORIGINAL TEXT NOT YET PROVIDED (asked user 2026-11-09). Also asked for actually-submitted docx (fallback manuscript/manuscript_CRST_submission_final.docx).

## Diagnosed root causes (old model, src/graded_roof/simulation.py)
- travel = 0.5*a*dt^2 from rest each step -> with dt=1800 s fraction=1 always: transport is all-or-nothing.
- Gauss-Seidel ridge->eave sweep: received mass re-tested same step -> cascade order artifact.
- Uniform (40,40): low mu, A=0 roof sheds every step; S=L=peak snowfall per step = 10 kg/m2/h*8 m*0.5 h = 40; at 0.25 h -> 20. Pure discretization artifact.
- Static threshold per area: m* = A/(g(sin th - mu cos th)) if tan th > mu_s; else never slides (unless near-melt mu drop). Adhesion irrelevant when tan th <= mu.
- Synthetic forcing left-point sampled; per-step snowfall = rate(t0)*dt.

## Revised model (v2) design decisions (fix BEFORE viewing optimized results)
- Two-timescale event-driven scheme: outer forcing step dt; within step constant snowfall rate (exact step integral of continuous-time Gaussian forcing via erf), temperature at midpoint, constant melt rate; friction (age, T) updated per step.
- Exact threshold-crossing times within step for retaining cells (linear mass growth) -> release at exact time, no overshoot.
- Released slab runout via Coulomb energy balance across cells: v^2 += 2 g (sin - mu_k cos) dx; stop where v^2<=0; deposit, re-test static -> cascade until quiescent. Dt-free, mass exact.
- Cells with zero static threshold (tan>mu_s, A=0): continuous stream routing (rates) to stop cell or eave.
- Primary S_event,max: events = maximal intervals of eave-outflow activity (impulses + stream rate >= q_min=1 kg m-1 h-1) merged when gap < tau_sep = 1 h; event mass = integral. Sensitivity: tau_sep 10 min/3 h; fixed-window S_W (W=1 h primary sensitivity, 10 min, 3 h). Old per-step S_max kept as historical diagnostic.
- Convergence: dt 1,0.5,0.25,0.125,0.0625 h; N 12,24,48,96. Criteria predefined in EVENT/CONVERGENCE docs.
- Constrained optimization: feasible encoding + repair; segments (<=7, >=3 cells of 24), integer-degree slopes in [2,45], |adjacent dslope|<=12, discrete classes (3). Modes: uniform (exhaustive slope x class), geometry (class fixed aged_coated_metal), surface (slope fixed 25), joint. 5 seeds, pop 48 x gen 45.
- Robustness: paired CRN perturbations friction, adhesion, density, snowfall, temperature.

## Progress log
- Done: tag crst-submitted-v1, PHASE_00, DOI verification (all 3 resolve; off-topic: mine roof rock beam, rockfall-bridge, debris flow), Japan evidence docs (MLIT 532 munis/50.8%/18.25M 14.5%; deaths 22 FY2023; ~90% during removal, ~90% >=65; Art.86(4) mu_b no reduction with snow stops; Art.86(6) 1 m reduction where removal customary; JMA normals Sapporo 479 cm, Aomori 567, Niigata 139).
- v2 model: src/graded_roof/simulation_v2.py, forcing_v2.py (15-s reference grid), optimization_v2.py (feasible encoding, max 7 segments). Probe: 0.23 s/design at 0.25 h with 2 workers.
- Convergence: scripts/r1_convergence.py -> results/r1/convergence/ (production_dt_choice.json).
- Next: scripts/r1_optimize.py (uniform exhaustive 132 + continuous uniform 6300 sensitivity; geometry/surface/joint x 5 seeds 48x45), robustness, figures, manuscript.
- Convergence done: all dt acceptable under pre-specified rule -> production dt = 1.0 h (coarsest). p95 rel S_event 2.9% at 1 h; isolated outliers up to 1333 kg/m (threshold-boundary designs). Pre-specified add-on (2026-11-09 before optimisation): all final nondominated designs re-evaluated at 0.0625 h and N=48; report changes.
- Optimisation launched: scripts/r1_optimize.py -> results/r1/optimization/, log results/r1/optimize_run.log
- Docs written: NUMERICAL_CONVERGENCE_AUDIT, SEMANTIC_CODE_AUDIT, PHYSICAL_PARAMETER_PROVENANCE.csv, PHYSICAL_BENCHMARK_AUDIT, PHYSICAL_EVIDENCE_GAP, WEATHER_FORCING_AUDIT (results/r1/weather/synthetic_summary.csv), analysis_deviations R1 items 6-11.
- Uniform constructable: smooth steep roofs: L 33-85, S_event 313-1374 (frequent small slabs merged by tau_sep=1h); 20 deg smooth: L=S=91.9; classes 1 (aged) ~ L=S>=130.
- TODO after optimisation: scripts/r1_analyze.py (fronts, HV, epsilon, matched, per-seed, budget sensitivity via generation history, 0.0625h recheck), r1_robustness.py, sensitivities (tau_sep, q_min, entrainment), figures, manuscript build, response letter.
