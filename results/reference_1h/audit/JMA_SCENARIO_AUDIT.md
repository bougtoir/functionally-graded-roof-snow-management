# JMA supplementary scenario audit

## Coverage and provenance

The retained official JMA snapshot contains 72 monthly daily-table HTML files:
four stations, three winters, and six months per winter. The evaluated stations
are Kutchan, Shinjo, Aomori, and Takada. Every station-winter pair has 181 or
182 days and zero missing temperature or snowfall days in the processed table.

All retained quantitative JMA files pass the acquisition-ledger checksum audit.
No unavailable historical provenance record is used as a quantitative input.

## Paired trade-offs

The selected uniform and joint nominal knees were evaluated under each of the
12 station-winters. In every pair, the joint design has lower one-day release
mass `S_max` and higher retained modeled mass `L_max`.

Across the 12 pairs:

- joint-to-uniform `L_max` ratios range from 1.21 to 11.62;
- joint-to-uniform `S_max` ratios range from 0.50 to 0.51;
- `S_max` reductions range from 48.96% to 50.00%;
- `L_max` increases range from 20.95% to 1061.86%.

These descriptive paired results do not justify a significance test. The
magnitudes are strongly station-winter dependent and represent a modeled
trade-off, not validation or general superiority.

## Interpretation boundary

JMA daily ground observations are scenario forcing. They are not roof-load,
roof-shedding, or roof-surface measurements. Daily forcing cannot resolve
subdaily release events, and snowfall depth is converted to mass using an
assumed fresh-snow density. The resulting `S_max` is maximum release in one
daily model interval and is not directly comparable to hourly production
`S_max`.

## Gate

Status: PASS. Table 9 must become a paired table with station names, ratios,
differences, and explicit daily-interval labeling.
