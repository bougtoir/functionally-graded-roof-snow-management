"""R1 robustness of nondominated designs under parameter and forcing uncertainty."""

from __future__ import annotations

import json
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from graded_roof.optimization_v2 import (
    constructability_from_config,
    design_from_segments,
    weather_set_v2,
)
from graded_roof.simulation_v2 import EventSpec, simulate_v2
from graded_roof.study import simulation_config

PARETO = Path("results/r1/pareto")
FRONT_FILES = [
    PARETO / f"front_{n}.csv" for n in ("uniform", "geometry", "surface", "joint", "combined")
]
OUT = Path("results/r1/robustness")
_W: dict = {}


def _lognormal(rng, cv, n):
    sigma = np.sqrt(np.log1p(cv**2))
    return rng.lognormal(-0.5 * sigma**2, sigma, n)


def samples(cfg: dict) -> pd.DataFrame:
    r = cfg["robustness"]
    cv = r["coefficient_of_variation"]
    rng = np.random.default_rng(r["seed"])
    n = r["samples"]
    return pd.DataFrame(
        {
            "sample": np.arange(n),
            "friction_factor": _lognormal(rng, cv["friction"], n),
            "adhesion_factor": _lognormal(rng, cv["adhesion"], n),
            "density_factor": _lognormal(rng, cv["fresh_snow_density"], n),
            "snowfall_factor": _lognormal(rng, cv["snowfall"], n),
            "temperature_offset_c": rng.normal(0.0, cv["temperature_sd_c"], n),
        }
    )


def _init(cfg, dt):
    _W.update(cfg=cfg, dt=dt, c=constructability_from_config(cfg), sim=simulation_config(cfg))


def _job(args):
    key, segs, smp = args
    cfg, c, sim = _W["cfg"], _W["c"], _W["sim"]
    d = design_from_segments(segs, c, key)
    d = replace(
        d,
        mu_static=d.mu_static * smp["friction_factor"],
        mu_kinetic=d.mu_kinetic * smp["friction_factor"],
        adhesion_pa=d.adhesion_pa * smp["adhesion_factor"],
    )
    s = replace(sim, initial_density_kg_m3=sim.initial_density_kg_m3 * smp["density_factor"])
    ws = weather_set_v2(
        cfg,
        _W["dt"],
        snowfall_factor=smp["snowfall_factor"],
        temperature_offset_c=smp["temperature_offset_c"],
    )
    res = [simulate_v2(d, w, s, EventSpec()) for w in ws]
    return {
        "segments": key,
        "sample": int(smp["sample"]),
        "l_max_kg_per_m": max(r.l_max_kg_per_m for r in res),
        "s_event_max_kg_per_m": max(r.s_event_max_kg_per_m for r in res),
        "s_window_1h_kg_per_m": max(r.s_window_max_kg_per_m[1.0] for r in res),
        "mass_balance_abs_max": max(abs(r.mass_balance_error_kg_per_m) for r in res),
    }


if __name__ == "__main__":
    import sys

    sys.path.insert(0, "scripts")
    from r1_analyze import parse

    cfg = yaml.safe_load(open("config/production.yaml"))
    dt = json.loads(Path("results/r1/convergence/production_dt_choice.json").read_text())[
        "production_dt_h"
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    smp = samples(cfg)
    smp.to_csv(OUT / "uncertainty_samples.csv", index=False)
    keys = sorted(set(pd.concat([pd.read_csv(f) for f in FRONT_FILES]).segments))
    jobs = [(k, parse(k), row) for k in keys for row in smp.to_dict("records")]
    with Pool(2, initializer=_init, initargs=(cfg, dt)) as pool:
        out = pd.DataFrame(pool.map(_job, jobs, chunksize=25))
    out.to_csv(OUT / "robustness_runs.csv", index=False)
    q = cfg["robustness"]["robust_quantile"]
    agg = out.groupby("segments").agg(
        l_q=("l_max_kg_per_m", lambda x: x.quantile(q)),
        s_q=("s_event_max_kg_per_m", lambda x: x.quantile(q)),
        s1h_q=("s_window_1h_kg_per_m", lambda x: x.quantile(q)),
        l_median=("l_max_kg_per_m", "median"),
        s_median=("s_event_max_kg_per_m", "median"),
        mass_balance_max=("mass_balance_abs_max", "max"),
    )
    agg.to_csv(OUT / "robustness_summary.csv")
    print(agg.round(1).to_string())
