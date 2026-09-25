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
| all three 1-h selected designs fail versus 0.5 h | PASS |
| all three 0.5-h selected designs fail targeted 0.25-h check | PASS |
| Lmax is defined as modeled mass rather than structural load | PASS |
| Smax is defined with its timestep | PASS |
| JMA is framed as scenario forcing | PASS |
| robustness intervals are not empirical confidence intervals | PASS |

## Headline-number trace

| Quantity | Canonical value fragment | Manuscript match |
|---|---:|---|
| uniform objective-pair count | only 2 objective pairs | PASS |
| joint objective-pair count | joint: 6 objective pairs | PASS |
| uniform hypervolume | 0.701 | PASS |
| joint hypervolume | 0.762 | PASS |
| joint descriptive knee Lmax | 4547.4 | PASS |
| joint descriptive knee Smax | 12.28 | PASS |
| robustness Q95 Lmax lower bound | 51.89 | PASS |
| robustness Q95 Lmax upper bound | 5816.7 | PASS |
| robustness tie count | shared by 6 candidates | PASS |
| mapping Lmax percent | -98.28 | PASS |
| mapping Smax percent | 537.47 | PASS |
| JMA Lmax ratio minimum | 2.84 | PASS |
| JMA Lmax ratio maximum | 16.68 | PASS |
| JMA Smax reduction minimum | 67.01 | PASS |
| JMA Smax reduction maximum | 70.83 | PASS |

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
- The 0.5-h frontier is the production numerical reference, not evidence of convergence beyond 0.5 h.
- The failed 1-h comparison and targeted 0.25-h sensitivity are both reported without changing Lmax or Smax definitions.
