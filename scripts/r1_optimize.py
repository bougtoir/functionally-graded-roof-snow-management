"""R1 constructability-constrained optimisation (uniform exhaustive + NSGA-II modes)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from graded_roof.optimization_v2 import (
    constructability_from_config,
    evaluate_many,
    run_constrained,
    uniform_constructable_segments,
)
from graded_roof.simulation_v2 import EventSpec
from graded_roof.study import simulation_config

OUT = Path("results/r1/optimization")
SEEDS = [1701, 2903, 4517, 6007, 8191]


def main(which: list[str]) -> None:
    cfg = yaml.safe_load(open("config/production.yaml"))
    dt = json.loads(Path("results/r1/convergence/production_dt_choice.json").read_text())[
        "production_dt_h"
    ]
    sim, spec = simulation_config(cfg), EventSpec()
    c = constructability_from_config(cfg)
    OUT.mkdir(parents=True, exist_ok=True)
    if "uniform" in which:
        df = evaluate_many(cfg, uniform_constructable_segments(c), dt_hours=dt, sim=sim, spec=spec)
        df.to_csv(OUT / "uniform_constructable_evaluated.csv", index=False)
        print("uniform", len(df), flush=True)
    if "uniform_continuous" in which:
        from multiprocessing import Pool

        from graded_roof.models import RoofDesign
        from graded_roof.optimization_v2 import evaluate_v2, weather_set_v2

        grid = [
            (s, m, a)
            for s in np.linspace(2, 45, 30)
            for m in np.linspace(0.08, 0.65, 30)
            for a in np.linspace(0, 250, 7)
        ]
        global _job

        def _job(p):
            s, m, a = p
            w = weather_set_v2(cfg, dt)
            d = RoofDesign.uniform(
                c.cells, c.length_m, s, m, m * cfg["surface"]["kinetic_ratio"], a
            )
            return {
                "slope_deg": s,
                "mu_static": m,
                "adhesion_pa": a,
                **evaluate_v2(d, w, sim, spec),
            }

        with Pool(2) as pool:
            rows = pool.map(_job, grid, chunksize=20)
        pd.DataFrame(rows).to_csv(OUT / "uniform_continuous_grid_evaluated.csv", index=False)
        print("uniform_continuous", len(rows), flush=True)
    for mode in ("geometry", "surface", "joint"):
        if mode not in which:
            continue
        for seed in SEEDS:
            if (OUT / f"{mode}_seed_{seed}_meta.json").exists():
                continue
            meta = run_constrained(
                cfg,
                mode,
                seed,
                dt_hours=dt,
                sim=sim,
                spec=spec,
                population=cfg["optimizer"]["population"],
                generations=cfg["optimizer"]["generations"],
                out_dir=OUT,
            )
            print(json.dumps(meta), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or ["uniform", "geometry", "surface", "joint", "uniform_continuous"])
