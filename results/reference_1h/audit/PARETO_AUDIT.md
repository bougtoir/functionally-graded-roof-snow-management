# Primary Pareto audit

## Reconstruction

All four stored fronts were reconstructed from their canonical CSV files with
both objectives treated as minimization targets. Objective pairs were rounded
to six decimal places solely for equality and duplicate handling; no objective
value was changed in the canonical files.

The files contain many nondominated **design rows** but few unique
`L_max`-`S_max` pairs:

- uniform: 2,912 design rows and 2 unique objective pairs;
- geometry-only: 320 rows and 15 pairs;
- surface-only: 1,731 rows and 2 pairs;
- joint: 1,928 rows and 8 pairs.

The multiplicity is scientifically relevant as design degeneracy, but it is not
objective-space resolution. Final figures and prose must report unique pairs
separately from design multiplicity.

## Dominance

After tolerance-aware duplicate handling:

- the surface-only objective set is the same as the uniform objective set;
- the joint set contains both uniform objective pairs and six additional
  nondominated trade-off pairs;
- geometry-only pairs other than the retention endpoint are dominated in the
  combined objective set.

Earlier row-level combined-set dominated fractions were unstable because
nominally identical floating-point values from different classes could differ
below reporting precision. The revised audit uses six-decimal objective
equality before dominance calculations.

## Hypervolume and epsilon

The original normalized hypervolume used a zero ideal and a reference equal to
105% of the largest observed objective. The audit additionally uses a common
observed-minimum origin and 105% and 110% reference margins. The qualitative
ranking is unchanged: joint has the largest hypervolume; uniform and surface
are equal; geometry is smaller.

Joint hypervolume can exceed uniform hypervolume while additive epsilon versus
uniform is zero because the joint unique set includes the two uniform objective
pairs exactly and adds six intermediate trade-off pairs. Epsilon zero means the
joint approximation can match each uniform reference point; it does not imply
that every joint design dominates every uniform design or that grading is
front-wide superior.

## Stochastic optimization

The heterogeneous results are approximate observed nondominated sets, not
complete fronts. Common-normalization per-seed metrics preserve the substantial
seed variation already visible in the original optimizer stochasticity table.
Pooling three seeds improves observed coverage but is not proof of global
convergence.

## Gate

Status: PASS with required reporting corrections. No canonical simulation was
altered. The final manuscript must replace “Pareto points” counts with explicit
design-row and unique-objective-pair counts and must not describe heterogeneous
fronts as complete.
