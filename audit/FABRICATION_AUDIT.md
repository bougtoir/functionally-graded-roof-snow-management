# Fabrication, numerical, and reference audit

Overall status: PASS

## Audit gates

| Gate | Status |
|---|---|
| figures 1-9 cited in order | PASS |
| tables 1-9 cited in order | PASS |
| nine figure captions present | PASS |
| nine table captions present | PASS |
| references use CRST author-year style | PASS |
| all listed references cited | PASS |
| reference list is alphabetical | PASS |
| reference audit rows match manuscript references | PASS |
| reference snapshots verified | PASS |
| reference titles verified | PASS |
| reference years verified | PASS |
| reference claims and transfer limits populated | PASS |
| all audited headline fragments present | PASS |
| number-provenance rows are verified | PASS |
| number-provenance sources exist | PASS |
| all three production-timestep designs fail | PASS |
| Lmax is defined as modeled mass rather than structural load | PASS |
| Smax is defined with its timestep | PASS |
| JMA is framed as scenario forcing | PASS |
| robustness intervals are not empirical confidence intervals | PASS |

## Headline-number trace

| Quantity | Canonical value fragment | Manuscript match |
|---|---:|---|
| uniform objective-pair count | only 2 objective pairs | PASS |
| joint objective-pair count | joint set contained 8 | PASS |
| uniform hypervolume | 0.402 | PASS |
| joint hypervolume | 0.611 | PASS |
| joint descriptive knee Lmax | 3210.6 | PASS |
| joint descriptive knee Smax | 40.00 | PASS |
| robustness Q95 Lmax lower bound | 103.8 | PASS |
| robustness Q95 Lmax upper bound | 7465.5 | PASS |
| robustness tie count | shared by 6 candidates | PASS |
| mapping Lmax percent | 0.36 | PASS |
| mapping Smax percent | 11.03 | PASS |
| JMA Lmax ratio minimum | 1.21 | PASS |
| JMA Lmax ratio maximum | 11.62 | PASS |
| JMA Smax reduction minimum | 48.96 | PASS |
| JMA Smax reduction maximum | 50.00 | PASS |

## Reference audit

- Manuscript references: 22.
- Verified reference snapshots: 22.
- Each audited record contains its supported claim, transfer limit, local snapshot path, and SHA-256.
- Machine-readable output: `references/reference_audit.csv`.

## Interpretation

- No synthetic output is represented as an observation.
- JMA ground observations are scenario forcing, not roof-load or roof-shedding validation.
- Generic mapped surface classes are not commercial product claims.
- Monte Carlo quantiles are conditional model outputs, not empirical confidence intervals.
- The 1-h production frontier remains explicitly qualified by the failed four-metric convergence criterion.
