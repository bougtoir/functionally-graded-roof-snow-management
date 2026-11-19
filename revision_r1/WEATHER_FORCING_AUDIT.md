# WEATHER_FORCING_AUDIT (R1)

## Synthetic winters (primary optimisation forcing; `src/graded_roof/forcing_v2.py`)
Defined in continuous time: Gaussian snowfall pulses (peak rate, number of pulses, centres between 12 % and 65 % of 336 h, σ = snowfall hours / pulses / 3), linear warming plus a 2 °C diurnal cycle, rain-on-snow placed uniformly over the last 12 h with T > −0.5 °C. Step totals are exact integrals (snowfall) or 15-s aggregates (rain, temperature mean), so every dt sees the same storm. Water-equivalent totals per winter are tabulated in `results/r1/weather/synthetic_summary.csv`.

## JMA station winters (supplementary scenarios)
Daily tables (Kutchan, Aomori, Shinjo, Takada; winters 2021–2023) in `data/raw/jma_daily/`; processed `data/processed/jma_daily_observations.csv`. JMA "--" (no phenomenon) is mapped to 0 and ")" / "]" quality flags are retained in the raw columns. Daily values cannot resolve sub-daily release timing; no sub-daily observations are invented. These are **scenario inputs, not validation of roof snow**.

## Hydrological processes
Rain-on-snow enters only as a melt-energy term (0.02 kg m⁻² per mm). Liquid-water retention, refreezing, runoff routing, gutter/drainage capacity and hydrologically triggered releases (wet-snow avalanching) are outside the model and are stated as limitations; the near-melt friction drop is the only wetness-related release mechanism.
