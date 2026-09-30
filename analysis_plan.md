# Analysis plan

## Scientific question and locked hypothesis

Under identical modeled environmental conditions, how does allowing spatial
variation in roof geometry and snow-surface interaction change the achievable
trade-off between retained roof snow load and discrete snow-shedding events
compared with optimized spatially uniform roofs?

The primary hypothesis is that spatial heterogeneity expands the attainable
design space. Superiority is not assumed; a null, conditional, or adverse result
will be reported without changing the model to rescue the hypothesis.

## Locked primary outcomes

- `L_max`: maximum modeled roof snow mass per metre roof width over time,
  sampled after interval snowfall is added but before interval melt and
  shedding. End-of-interval retained mass remains a separate time series.
- `S_max`: maximum mass leaving the eave in one simulation timestep per metre
  roof width.
- Primary comparison: nondominated optimized uniform and heterogeneous design
  sets in the `L_max`–`S_max` plane.

Modeled snow mass is not described as a code-level structural load. `SSCI`, total
shed mass, event count, event-mass summaries, kinetic-energy proxy, threshold
time, intervention triggers, residual mass, and design complexity are secondary.

## Comparators

1. Optimized uniform retention-oriented roofs.
2. Optimized uniform shedding-oriented roofs.
3. The complete optimized uniform intermediate frontier.
4. Geometry-only heterogeneous roofs.
5. Surface-only heterogeneous roofs.
6. Joint geometry-and-surface heterogeneous roofs.

Hand-picked exemplars are illustrative only and never replace the optimized
uniform frontier.

## Model and weather

The roof is a ridge-to-eave plane divided into `N` cells. Each cell has slope,
static friction, kinetic friction, and adhesion. Snowfall adds mass; a
force-balance threshold initiates motion; kinetic friction controls transport;
temperature and age modify snow state through prespecified functions. Melt and
rain-on-snow are included only as configured scenario processes. Snow density
controls the diagnostic snow-depth state and converts JMA snowfall-depth
observations to mass; at fixed mass it is not asserted to alter basal sliding.

Synthetic scenarios span snowfall intensity and duration, temperature, warming,
repeated snowfall, and rain-on-snow. Official JMA observations from contrasting
heavy-snow stations and winters are scenario evaluations rather than validation.

## Optimization and Pareto analysis

The production optimizer is NSGA-II with deterministic independent seeds.
Uniform designs are mapped before heterogeneous optimization. Report complete
nondominated sets, dominated fraction, normalized hypervolume, additive epsilon,
and matched-objective improvement. Optimizer stochasticity is summarized across
seeds; simulation replication is not used to manufacture small p-values.

## Convergence and resolution

Test multiple `N` and `dt` values using fixed designs and scenarios. Select the
coarsest production resolution meeting frozen relative-change tolerances for
`L_max`, `S_max`, event count, and SSCI while retaining feasible runtime.

## Sensitivity, robustness, and ablation

Prespecified sensitivity dimensions are static/kinetic friction, adhesion,
fresh-snow density for depth-to-mass conversion and modeled depth, aging rate,
temperature, snowfall intensity, roof length, `N`, `dt`,
slope bounds, adjacent-slope bounds, transition penalty, rain-on-snow, and
constant versus dynamic friction. Monte Carlo perturbations estimate
distributions for selected uniform and heterogeneous Pareto designs. Analyses
also constrain segment length and transitions, map continuous friction to
documented generic classes, and measure discretization loss.

## Strategy classification and labor scarcity

Classification rules are frozen before phase-diagram production. The classes
are `RETENTION`, `UNIFORM_INTERMEDIATE`, `SHEDDING`, and `GRADED_HYBRID`, based
on design heterogeneity, retained mass, and shedding behavior using configured
thresholds. Labor scarcity enters only as configurable low/medium/high
decision-weight scenarios; it is not assigned to real communities.

## Missing parameters and evidence

Every physical value must have a verified source or be labeled an assumption.
Unsupported quantities remain sensitivity parameters. No proprietary material
performance is invented. Missing weather observations remain missing unless a
prespecified transparent transformation is justified.

## Figure plan

1. Concept and competing passive strategies.
2. Model and force balance.
3. Representative synthetic and JMA winters.
4. Primary uniform-versus-heterogeneous Pareto frontier.
5. Selected spatial profiles.
6. Ablation and complexity/discretization effects.
7. Sensitivity and Monte Carlo robustness.
8. Strategy phase diagram and labor-scarcity scenarios.

## Conclusion rules and scope limits

Conclusions follow effect magnitudes and uncertainty. The manuscript will not
claim structural safety, pedestrian safety, code compliance, actual injury
reduction, universal lifecycle cost, universal superiority, or effectiveness in
every snow climate. Japanese scenarios will not be generalized beyond their
modeled context.

## Reproducibility

All numerical manuscript values, figures, and tables are generated from
machine-readable results. Raw public data are retained with a checksum ledger.
`make all` runs critical validation and packaging. Deviations after freeze are
recorded in `analysis_deviations.md`.
