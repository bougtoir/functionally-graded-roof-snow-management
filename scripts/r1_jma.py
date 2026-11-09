"""R1 supplementary evaluation of nondominated designs under observed JMA daily station winters.

Daily values are spread uniformly over 24 h (temperature held constant within a day); this is a
scenario-forcing assumption, not a sub-daily reconstruction and not roof-snow validation.
"""

from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from graded_roof.jma import daily_weather
from graded_roof.models import WeatherSeries
from graded_roof.optimization_v2 import constructability_from_config, design_from_segments
from graded_roof.simulation_v2 import EventSpec, simulate_v2
from graded_roof.study import simulation_config

PARETO = Path("results/r1/pareto")
OUT = Path("results/r1/jma")
_W: dict = {}


def hourly(w: WeatherSeries) -> WeatherSeries:
    n = 24
    return WeatherSeries(
        temperature_c=np.repeat(w.temperature_c, n),
        snowfall_kg_m2=np.repeat(w.snowfall_kg_m2 / n, n),
        rain_mm=np.repeat(w.rain_mm / n, n),
        dt_hours=1.0,
        name=w.name,
    )


def _init(cfg, ws):
    _W.update(c=constructability_from_config(cfg), sim=simulation_config(cfg), ws=ws)


def _job(args):
    key, segs = args
    d = design_from_segments(segs, _W["c"], key)
    rows = []
    for w in _W["ws"]:
        r = simulate_v2(d, w, _W["sim"], EventSpec())
        rows.append(
            {
                "segments": key,
                "station_winter": w.name,
                "l_max_kg_per_m": r.l_max_kg_per_m,
                "s_event_max_kg_per_m": r.s_event_max_kg_per_m,
                "s_window_1h_kg_per_m": r.s_window_max_kg_per_m[1.0],
                "event_count": r.event_count,
                "mass_balance_abs": abs(r.mass_balance_error_kg_per_m),
            }
        )
    return rows


if __name__ == "__main__":
    sys.path.insert(0, "scripts")
    from r1_analyze import parse

    cfg = yaml.safe_load(open("config/production.yaml"))
    obs = pd.read_csv("data/processed/jma_daily_observations.csv")
    rho = cfg["snow"]["initial_density_kg_m3"]
    ws = [
        hourly(daily_weather(g.sort_values("date"), fresh_snow_density_kg_m3=rho, name=f"{s}_{y}"))
        for (s, y), g in obs.groupby(["station_id", "winter"])
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "station_winter": w.name,
                "days": len(w.temperature_c) // 24,
                "snowfall_we_kg_m2": w.snowfall_kg_m2.sum(),
                "rain_mm": w.rain_mm.sum(),
                "t_mean_c": w.temperature_c.mean(),
            }
            for w in ws
        ]
    ).to_csv(OUT / "jma_forcing_summary.csv", index=False)
    allev = pd.read_csv(PARETO / "all_evaluated_designs.csv").drop_duplicates("segments")
    uni = allev[allev["mode"] == "uniform"].segments.tolist()
    front = set(pd.concat([pd.read_csv(f) for f in PARETO.glob("front_*.csv")]).segments)
    keys = sorted(set(uni) | front)
    with Pool(2, initializer=_init, initargs=(cfg, ws)) as pool:
        rows = [
            r for chunk in pool.map(_job, [(k, parse(k)) for k in keys], chunksize=4) for r in chunk
        ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "jma_runs.csv", index=False)
    print(out.groupby("station_winter")[["l_max_kg_per_m", "s_event_max_kg_per_m"]].max())
