# EVENT_METRIC_SPECIFICATION — physical shedding events (R1)

Status: specified 2026-11-09 before any revised optimisation, robustness or manuscript result was generated. Implemented in `src/graded_roof/simulation_v2.py` (`segment_events`, `max_window_mass`).

## 1. Why the submitted endpoint is replaced
The submitted `S_max` was the largest eave outflow in one numerical step. Because the submitted transport moved a fixed fraction of a failing cell per step (with `dt = 0.5 h` the fraction was always 1) and the per-step value scales with `dt`, `S_max` measured the step length rather than a physical release (targeted check: uniform knee 40.0 → 20.0 kg m⁻¹ from 0.5 h to 0.25 h). It is retained only as the historical diagnostic `legacy_s_step_max_kg_per_m`.

## 2. Eave outflow record (continuous time)
- **Slab impulse**: a cell whose retained mass reaches its static threshold `m* = c·A_cell/(g(sin θ − μs cos θ))` releases at the exact crossing time (forcing is piecewise constant within a step, so the crossing is solved analytically). The slab moves as a Coulomb block (`v² ← v² + 2g(sin θ − μk cos θ)Δx`), entrains resting snow in traversed cells (perfectly inelastic), and either deposits where `v² ≤ 0` or leaves the eave as one impulse with time, mass and kinetic energy.
- **Stream segment**: cells with `m* = 0` (no adhesion and `tan θ > μs`) cannot retain snow; their snowfall is routed continuously; when routed to the eave it is logged as a constant-rate segment `[t0, t1]` with mass.
- **Simultaneous releases**: all releases at the same instant (|Δt| < 1e-9 h) are processed ridge→eave; impulses at the same time are separate records but always fall into one event.

## 3. Event definition (primary)
- **Activity**: every slab impulse, and every stream segment with rate ≥ `q_min = 1.0 kg m⁻¹ h⁻¹`.
- **Initiation**: first activity after a quiescent gap ≥ `τ_sep`.
- **Merging / termination**: activity intervals separated by a gap `< τ_sep = 1.0 h` belong to the same event; the event ends at the end of its last activity interval. Events are never split inside activity.
- **Low-flow intervals**: stream outflow below `q_min` does not initiate or extend an event but its mass is counted when it lies inside an event interval; low flow outside events is reported in total shed only.
- **Event mass**: `M_e = Σ impulses in [t_e0, t_e1] + ∫ stream rate over [t_e0, t_e1]`.
- **Primary endpoint**: `S_event,max = max_e M_e` (kg m⁻¹), worst case over the three synthetic winters.
- **Numerical tolerance**: time 1e-9 h; mass 1e-12 kg.

## 4. Secondary / sensitivity endpoints
- `S_W,max`: largest eave outflow in any closed window of length W ∈ {10 min, 1 h, 3 h} (dt-independent by construction; 1 h is the intensity-type co-reported endpoint).
- `τ_sep` sensitivity: 10 min and 3 h; `q_min` sensitivity: 0.1 and 10 kg m⁻¹ h⁻¹.
- Event count, event duration, event-level SSCI (Σ (M_e/ΣM)²), maximum slab kinetic energy at the eave per event, total shed, time above the 800 kg m⁻¹ intervention mass, triggers.
- Entrainment sensitivity: slab without entrainment.

## 5. Pre-specified numerical-convergence criteria
Reference: `dt_ref = 0.0625 h`, N = 24 (spatial check at N = 48, 96 with segment lengths scaled).
For each panel design × scenario and each of `L_max`, `S_event,max`, `S_1h,max`, total shed: agreement with the reference if `|X − X_ref| ≤ max(0.02|X_ref|, 1 kg m⁻¹)`.
A step is **acceptable for production** when ≥ 95 % of panel pairs agree for every metric, and event counts differ by ≤ 1 in ≥ 90 % of pairs. The coarsest acceptable step from {1, 0.5, 0.25, 0.125} h is used for optimisation; if none qualifies the finest computationally feasible step is used and the failure is reported. Mass-balance error must be < 1e-6 kg m⁻¹ for every run.
Panel: all 132 constructable uniform roofs plus 60 constructable graded roofs drawn with seed 9001 (20 each from the geometry, surface and joint encodings).
