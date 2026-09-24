# Skeptical CRST physics review: functionally graded roof snow management

**Review basis.** I inspected the public repository at commit `c1789fecbbb5cf944c4ddc7665457354416f8187`. It contains only a one-line project description and a license: there are no equations, source code, parameter files, forcing data, calibration/validation data, results, manuscript, or optimizer configuration. Consequently, this is a review of the **proposed model class**, not an audit of an implemented model.

## Bottom line

**Current status: not reviewable as a scientific submission.** A 2D cell model can support a useful *computational proof of concept*, but maximum single-event shedding mass is not determined by static force balance alone. It depends on how basal sliding, internal fracture, kinetic motion, event propagation, and event aggregation are represented. Unless those mechanisms and their scale dependence are explicit, the apparent Pareto front may primarily measure discretization and update rules.

**Potentially publishable after major development** if the authors (i) formulate a dimensionally consistent and mesh-objective model; (ii) validate relevant thresholds and event behavior against independent roof–snow data; (iii) demonstrate spatial, temporal, event-detection, and Pareto-front convergence; (iv) use optimized, budget-matched controls; (v) report stochastic optimizer performance rather than one favorable run; and (vi) restrict conclusions to conditional model behavior. The scientific novelty must be a robust mechanistic insight about spatial grading—not merely application of NSGA-II.

## 1. Minimum defensible physics

### 1.1 State, forcing, and conservation

At minimum, define for every cell \(i\): plan area, slope and aspect; snow thickness \(h_i\), density \(\rho_i\), mass \(m_i\), temperature or an explicitly justified surrogate, liquid-water state, basal state, internal bond state, and—if inertial motion is claimed—velocity. State all units and whether the 2D model represents an areal roof, a unit-width slice, or a depth-averaged layer.

Write the vector force balance explicitly. For a simple downslope direction, the driving term should expose \(m_i g\sin\theta\) plus declared neighbor/contact forces, while the normal balance should expose at least \(m_i g\cos\theta\) and any other normal interactions. Release should follow a stated inequality between driving demand and available resistance—not an order-dependent transfer rule hidden in code.

Snowfall, rain, melt/refreeze, runoff, roof heat flux, radiation, ambient temperature, and wind redistribution must either enter a mass/energy balance or be explicitly excluded. Published roof-slide simulations show that climate, neighboring-building shielding, and interior heat transfer can change sliding predictions; therefore a purely mechanical threshold with fixed material constants cannot support general climatic claims ([Zhou et al., 2013](https://doi.org/10.1007/s11069-013-0563-8)).

Every time step and shedding event should close:

\[
M(t+\Delta t)=M(t)+M_{\mathrm{snow}}+M_{\mathrm{rain}}-M_{\mathrm{runoff}}-M_{\mathrm{melt\,loss}}-M_{\mathrm{shed}},
\]

to numerical tolerance, with no disappearance or duplication during cascades.

### 1.2 Distinguish basal sliding from internal snow failure

A defensible local basal criterion may be written in stress form,

\[
\tau_{b,\max}=c_b+\mu_s\sigma_n,
\]

or equivalently in force form \(R_b=c_bA_i+\mu_sN_i\), where \(c_b\) is roof–snow adhesion/interfacial cohesion and \(\mu_s\) is static friction. These are not interchangeable with internal snow cohesion or tensile/shear bond strengths. The model must separately define:

1. **roof–snow interface failure** (sliding or release at the substrate);
2. **snow–snow shear/tensile failure** between cells or layers;
3. **post-failure motion and arrest**;
4. **boundary restraint**, discontinuities, eaves, ridges, and any snow-retention device.

This separation is essential because measured roof–snow behavior varies strongly with roof material and thermal condition. Bartko and Baskaran reported material-dependent sliding angles over a broad range in commercial roof tests ([2018](https://doi.org/10.1061/%28ASCE%29CR.1943-5495.0000146)); Cao et al. measured roof–snow interface shear strengths spanning roughly \(0.15\)–\(2.00\ \mathrm{kPa}\) over their tested substrates and temperatures and found substrate- and temperature-dependent behavior ([2024](https://doi.org/10.3390/buildings14041036)). These ranges are **study-specific**, not universal parameter bounds, but they rule out treating one friction/cohesion constant as generally valid.

### 1.3 Static threshold is insufficient for event size

For dry, cohesionless, uncoupled snow, the limiting check should reduce to \(\tan\theta=\mu_s\). However, once release begins, single-event mass depends on:

- static-to-kinetic friction transition;
- inertia or an explicitly quasi-static propagation rule;
- bond breaking and load redistribution;
- collision/entrainment between cells;
- arrest and reattachment rules;
- numerical simultaneity/update ordering;
- the temporal and spatial definition of “one event.”

A cellular cascade model may be acceptable as a stylized proof of concept, but it must be labeled as such and its propagation law must be calibrated or bracketed. If only incipient motion is modeled, the output is a **released unstable mass**, not a physically validated shed-event mass.

### 1.4 Mesh-objective constitutive scaling

For cell size \(\Delta x\), body force scales with cell area (or volume), basal traction with basal area, and intercell force with shared edge area/length under the declared dimensional interpretation. Bond energy or fracture resistance cannot be a fixed per-neighbor number independent of resolution. The manuscript must derive the scaling and show that rotating or refining the grid does not change the physics. Snow deformation and fracture are nonlinear, microstructure-dependent, and spatially variable; a lattice rule without a continuum or experimentally calibrated interpretation is not enough ([Shapiro et al., 1997](https://doi.org/10.21236/ADA330695); [Schweizer et al., 2003](https://doi.org/10.1029/2002RG000123)).

## 2. Verification, validation, and sanity tests

Verification (solving the stated model correctly) must be kept separate from validation (agreement with physical observations), following established computational V&V practice ([Oberkampf et al., 2004](https://doi.org/10.1115/1.1767847)).

| Level | Minimum test | Pass criterion |
|---|---|---|
| Dimensional/unit | Unit audit of every force, stress, energy, and flux | No resolution-dependent or mixed force/stress parameters |
| Analytic limits | Flat roof; frictionless roof; dry cohesionless slope; zero snowfall/melt; infinite adhesion; uncoupled cells | Correct no-motion, immediate-motion, and \(\tan\theta=\mu_s\) limits |
| Symmetry/invariance | Uniform roof under uniform forcing; mirrored layout; translated pattern; rotated lattice where physically equivalent | Symmetric outputs and no preferred grid direction beyond stated geometry |
| Conservation | Mass budget before, during, and after multi-cell cascades | Residual reported and negligible relative to event mass |
| Event logic | Hand-solvable two-cell and small-grid cases; simultaneous failures; competing cascades | Exact expected released cells and deterministic tie handling |
| Mechanism ablation | Disable adhesion, cohesion, kinetic motion, thermal forcing, and redistribution separately | Changes are physically interpretable, not algorithmic surprises |
| Interface validation | Independent sliding-angle or direct-shear data across relevant roof materials/temperatures | Thresholds and uncertainty intervals reproduced without using validation cases for fitting |
| System validation | Instrumented small roof or published field/lab sequence with retained mass and release timing/event size | Predeclared metrics and prediction intervals; calibration/validation split |

Building standards and design coefficients are useful external context, but matching a code coefficient is not physical validation. ISO 4355 explicitly treats roof snow intensity/distribution and partial loading from melting, sliding, redistribution, and removal; this supports the relevance of the processes, not the correctness of a new event model ([ISO 4355:2013](https://www.iso.org/standard/56059.html)).

## 3. Numerical convergence requirements

1. **Spatial refinement:** use at least three systematically refined grids over the same physical roof and the same continuous material field. Report \(J_R\), \(J_S\), event count, timing, released footprint, conservation residual, and computational cost.
2. **Time/event refinement:** repeat with smaller \(\Delta t\), event-detection tolerances, and alternative defensible event-merging windows. Disclose whether failures update synchronously or sequentially and test sensitivity to ordering and tie-breaking.
3. **Lattice sensitivity:** compare orientations and, if relevant, neighborhood topologies. A checkerboard or channel aligned to the grid must not receive unearned performance.
4. **Optimization under refinement:** re-run the optimization at each resolution. Merely reevaluating a coarse-grid optimum on a fine grid does not show convergence of the optimum or Pareto set.
5. **Front convergence:** quantify changes in normalized hypervolume, IGD+ or a declared set-distance, extreme points, knee regions, and design rank reversals. Show whether claimed dominance survives refinement.
6. **Discontinuous observables:** maximum event mass is generally nonsmooth. Use convergence envelopes, quantiles, and rank stability rather than forcing Richardson/GCI estimates where the asymptotic smooth regime is absent. For sufficiently smooth observables, report refinement ratios, observed order, extrapolated value, and uncertainty in the style of Roache ([1994](https://doi.org/10.1115/1.2910291)).

Numerical uncertainty must be smaller than the claimed benefit over controls; otherwise the central comparative conclusion is unresolved.

## 4. Fair comparator design

All comparators must use the same roof geometry, material bounds, total material/cost budget, manufacturability constraints, weather realizations, event definition, and simulation fidelity.

**Required controls:**

- **optimized uniform roof**, not an arbitrary nominal material;
- **optimized monotone gradient** with the same allowed range and material budget;
- **two-/few-zone designs**, establishing whether a complex field adds value over simple segmentation;
- **spatially permuted controls** with the same histogram of local properties, testing whether arrangement—not merely composition—causes benefit;
- **random/space-filling layouts** under identical constraints;
- **small-instance exhaustive or near-exhaustive enumeration**, where feasible, to benchmark optimizer reliability;
- **conventional retention/segmentation controls** only if their mechanics and costs are represented fairly.

Lower-dimensional controls should be optimized to near-global quality; imposing the same heuristic on every design class can unfairly handicap simple baselines. Conversely, higher-dimensional graded designs must pay an explicit complexity/manufacturing cost or constraint. Use common weather realizations/random numbers for paired comparisons and report effect distributions, not only best cases. Include physics ablations to show which mechanism creates the trade-off.

## 5. Objective and optimizer reporting

Define the objectives mathematically, for example:

\[
J_R=\max_{t\in[0,T]} M_{\mathrm{roof}}(t), \qquad
J_S=\max_{e\in\mathcal E} M_{\mathrm{shed},e},
\]

and state whether both are minimized. Specify horizon \(T\), warm-up, storm separation, treatment of snow remaining at \(T\), event gap/window, domain boundary crossing, and what happens when no shedding occurs. Report local peak load as an additional safety-relevant output; total retained mass alone can conceal dangerous concentration.

NSGA-II is a reasonable search method but is not evidence that the returned front is correct ([Deb et al., 2002](https://doi.org/10.1109/4235.996017)). Report:

- encoding, operators, repair/constraint handling, population, generations, stopping rule, and total model evaluations;
- multiple independent seeds and convergence traces;
- feasibility rate and duplicates;
- the complete nondominated approximation, not selected showcase designs;
- median and dispersion of hypervolume with fixed normalization and a predeclared reference point;
- IGD+ or another complementary distance metric against a transparently constructed reference set;
- empirical/summary attainment surfaces for stochastic runs;
- objective-wise uncertainty intervals for representative designs.

No single indicator is sufficient for optimizer comparison ([Zitzler et al., 2003](https://doi.org/10.1109/TEVC.2003.810758)). Attainment surfaces reveal run-to-run reliability ([Knowles, 2005](https://doi.org/10.1109/ISDA.2005.15)). Hypervolume results can change with the reference point, which must be declared and sensitivity-tested ([Ishibuchi et al., 2018](https://doi.org/10.1162/evco_a_00226)).

## 6. Robustness and uncertainty

At minimum, propagate uncertainty in snowfall sequence/intensity, wind redistribution, ambient and roof temperature, liquid water, snow density/layering, aging/sintering, \(\mu_s\), \(\mu_k\), basal adhesion, internal strength, slope, roof heat transfer, boundary restraint, and manufactured property deviations.

Required analyses:

1. **Out-of-sample forcing:** optimize on one ensemble or set of winters and evaluate on withheld climates/events; do not optimize and test on identical traces.
2. **Global sensitivity:** screen broadly, then quantify dominant parameters and interactions; one-at-a-time perturbations alone are inadequate near failure thresholds.
3. **Joint uncertainty:** preserve plausible correlations, especially temperature–melt–liquid-water–strength coupling.
4. **Manufacturing robustness:** perturb property magnitudes, zone boundaries, smoothing radius, and defects; enforce realizable spatial gradients.
5. **Tail behavior:** report upper quantiles or CVaR of retained and event mass where hazard reduction is discussed, not means alone.
6. **Decision stability:** give probability of dominance, Pareto-rank changes, and whether recommended patterns remain feasible and useful across scenarios.
7. **Structural/model-form alternatives:** repeat key conclusions under at least two defensible release/propagation laws. A conclusion that disappears under another plausible law is hypothesis-generating, not robust.

Robust multi-objective efficiency is not unique under uncertainty; the chosen concept—expected, worst-case/min–max, chance-constrained, CVaR, set-based, or another—must be stated and justified ([Ide and Schöbel, 2016](https://doi.org/10.1007/s00291-015-0418-7)).

## 7. Overclaim risks

| Claim risk | Defensible wording |
|---|---|
| “The roof is safer” | “Under the stated model and forcing ensemble, the design reduced the two simulated mass objectives.” |
| “Maximum event mass predicts ground hazard” | Event mass is only a proxy unless fall trajectory, fragmentation, velocity, impact area/energy, and exposure are modeled or measured. |
| “Maximum retained mass predicts structural safety” | Total mass is not a substitute for spatial load, drift, local demand, load combinations, or code checks. |
| “The model is validated” | Use “calibrated” or “compared with” unless independent experiments test quantities relevant to the final claims. |
| “The optimal pattern is general” | It is conditional on admissible designs, model form, parameter distributions, weather ensemble, objective definitions, and optimizer budget. |
| “Functionally graded material performance is demonstrated” | A numerical property field is not evidence that a manufacturable, durable roof surface realizes those properties. |
| “Code compliance/risk reduction” | Not supportable without structural design checks, prescribed load combinations, reliability analysis, and jurisdiction-specific review. |

All numerical examples must be labeled simulated. Parameter provenance must distinguish measured, literature-derived, calibrated, assumed, and optimized values.

## 8. Conditions for CRST publishability as a computational proof of concept

I would consider the study publishable only if all five conditions are met:

1. **Transparent model:** complete equations, units, parameter provenance, event definition, algorithms/pseudocode, and reproducible code/input data; basal and internal failure are separated.
2. **Credible V&V ladder:** analytic tests and conservation; independent interface data; and at least one system-level retained/release comparison or, if unavailable, explicit model-form bracketing and much narrower claims.
3. **Numerical objectivity:** spatial/time/lattice/event convergence and Pareto-front re-optimization, with discretization uncertainty smaller than the reported improvement.
4. **Fair and repeatable optimization:** strong budget-matched controls, multiple seeds, complementary quality indicators, attainment analysis, and out-of-sample robustness.
5. **Constrained interpretation:** conclusions framed as mechanistic hypotheses and conditional computational evidence, not engineering validation or safety assurance.

A publishable contribution would show, with uncertainty, **why** a reproducible spatial motif changes the retention–release trade-off, when it fails, and whether the motif survives resolution, climate, parameter, and manufacturing perturbations.

## 9. Prioritized revision plan

| Priority | Action | Severity if absent | Expected benefit | Feasibility |
|---|---|---:|---:|---:|
| P0 | Publish equations, units, event algorithm, parameter provenance, code, and inputs | Fatal | Very high | High |
| P0 | Separate basal sliding, internal fracture, and post-release dynamics/quasi-dynamics | Fatal | Very high | Medium |
| P0 | Complete analytic, conservation, event-logic, mesh/time/lattice tests | Fatal | Very high | Medium |
| P0 | Validate thresholds and at least bracket event propagation with independent data | Fatal | Very high | Medium–low |
| P1 | Re-optimize on refined grids and quantify Pareto-front stability | Major | Very high | Medium |
| P1 | Add optimized uniform/zoned/monotone/permuted controls | Major | High | High |
| P1 | Add multi-seed attainment, hypervolume sensitivity, and complementary metrics | Major | High | High |
| P1 | Run out-of-sample weather, joint parameter, model-form, and manufacturing robustness | Major | Very high | Medium |
| P2 | Add local load, release footprint, and impact-relevant proxy outputs | Important | High | Medium |
| P2 | Demonstrate a manufacturable graded surface and durability envelope | Important for application claims | High | Low–medium |

## Verification table

Confidence indicates confidence that the cited source supports the listed claim—not confidence that the proposed model is valid.

| Source | Identifier/DOI | Claim supported | Verification URL | Confidence |
|---|---|---|---|---|
| ISO, *Bases for design of structures—Determination of snow loads on roofs* (2013) | ISO 4355:2013 | Roof snow assessment includes load intensity/distribution and partial loading associated with melting, sliding, redistribution, removal, surface, exposure, and thermal effects. | [ISO record](https://www.iso.org/standard/56059.html) | High for scope; full standard not freely verified |
| Taylor, *Sliding Snow on Sloping Roofs* (1983) | NRC CBD-228 | Sliding depends on roof slope/material, snow conditions, meltwater/interface conditions, and obstruction/restraint; sliding snow creates hazards and load redistribution. | [NRC-IRC digest](https://web.mit.edu/parmstr/Public/NRCan/CanBldgDigests/cbd228_e.html) | High |
| Bartko & Baskaran, *Snow Friction Coefficient for Commercial Roofing Materials* (2018) | [10.1061/(ASCE)CR.1943-5495.0000146](https://doi.org/10.1061/%28ASCE%29CR.1943-5495.0000146) | Roof–snow friction/sliding angle is material-dependent; one universal coefficient is not defensible. | [DOI](https://doi.org/10.1061/%28ASCE%29CR.1943-5495.0000146) | High for tested materials; external validity limited |
| Cao et al., *Experimental Study on Shear Strength of Roof–Snow Interfaces* (2024) | [10.3390/buildings14041036](https://doi.org/10.3390/buildings14041036) | Interface shear strength depends on roof substrate and temperature; direct-shear data can inform sliding thresholds. | [Publisher](https://www.mdpi.com/2075-5309/14/4/1036) | High for reported experiments |
| Zhou et al., *Simulation method of sliding snow load on roofs…* (2013) | [10.1007/s11069-013-0563-8](https://doi.org/10.1007/s11069-013-0563-8) | Roof-slide prediction has been coupled to mass/energy balance, liquid-water state, climate, shielding, and interior heat transfer. | [Publisher abstract](https://link.springer.com/article/10.1007/s11069-013-0563-8) | High for model scope; moderate for generalization |
| Shapiro et al., *Snow Mechanics: Review of the State of Knowledge and Applications* (1997) | [10.21236/ADA330695](https://doi.org/10.21236/ADA330695) | Snow mechanics requires nonlinear deformation/fracture descriptions and constitutive relations linked to physical properties and microstructure. | [DOI](https://doi.org/10.21236/ADA330695) | High |
| Schweizer, Jamieson & Schneebeli, *Snow avalanche formation* (2003) | [10.1029/2002RG000123](https://doi.org/10.1029/2002RG000123) | Fracture initiation and propagation are distinct from simple basal friction and matter for release behavior. | [DOI](https://doi.org/10.1029/2002RG000123) | High for snow-fracture principle; indirect for roofs |
| Oberkampf, Trucano & Hirsch, *Verification, validation, and predictive capability…* (2004) | [10.1115/1.1767847](https://doi.org/10.1115/1.1767847) | Verification and validation are distinct; predictive claims require explicit treatment of numerical and physical-model evidence. | [DOI](https://doi.org/10.1115/1.1767847) | High |
| Roache, *A Method for Uniform Reporting of Grid Refinement Studies* (1994) | [10.1115/1.2910291](https://doi.org/10.1115/1.2910291) | Systematic grid refinement and observed-order/error reporting are required for numerical credibility where asymptotic convergence applies. | [DOI](https://doi.org/10.1115/1.2910291) | High |
| Deb et al., *NSGA-II* (2002) | [10.1109/4235.996017](https://doi.org/10.1109/4235.996017) | NSGA-II is an established elitist multi-objective evolutionary algorithm; its use does not itself establish optimality. | [DOI](https://doi.org/10.1109/4235.996017) | High |
| Zitzler et al., *Performance assessment of multiobjective optimizers* (2003) | [10.1109/TEVC.2003.810758](https://doi.org/10.1109/TEVC.2003.810758) | Approximation-set quality is multidimensional; optimizer assessment should not rely on one unqualified indicator. | [DOI](https://doi.org/10.1109/TEVC.2003.810758) | High |
| Knowles, *Summary-attainment-surface plotting…* (2005) | [10.1109/ISDA.2005.15](https://doi.org/10.1109/ISDA.2005.15) | Attainment surfaces visualize the distribution of stochastic multi-objective optimizer outcomes. | [DOI](https://doi.org/10.1109/ISDA.2005.15) | High |
| Ishibuchi et al., *How to Specify a Reference Point in Hypervolume Calculation…* (2018) | [10.1162/evco_a_00226](https://doi.org/10.1162/evco_a_00226) | Hypervolume comparisons depend on reference-point placement; fair comparisons require a declared, justified point and sensitivity analysis. | [DOI](https://doi.org/10.1162/evco_a_00226) | High |
| Ide & Schöbel, *Robustness for uncertain multi-objective optimization* (2016) | [10.1007/s00291-015-0418-7](https://doi.org/10.1007/s00291-015-0418-7) | Multiple non-equivalent robustness concepts exist for uncertain multi-objective optimization; the adopted concept must be explicit. | [Publisher/metadata](https://link.springer.com/article/10.1007/s00291-015-0418-7) | High |

**Evidence boundary.** I verified bibliographic metadata and available abstracts/open text for the claims above. I did not infer results from inaccessible full texts. The ISO file checked was a preview, not the complete standard. No empirical value from these sources should be transferred into the proposed model without confirming specimen, surface, thermal, loading, and scale compatibility.
