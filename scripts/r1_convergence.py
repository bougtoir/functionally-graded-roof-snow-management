"""R1 numerical convergence study (pre-specified in EVENT_METRIC_SPECIFICATION.md)."""

from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from graded_roof.optimization_v2 import (
    Constructability,
    constructability_from_config,
    decode,
    design_from_segments,
    evaluate_v2,
    n_variables,
    uniform_constructable_segments,
    weather_set_v2,
)
from graded_roof.simulation_v2 import EventSpec
from graded_roof.study import simulation_config

OUT = Path("results/r1/convergence")
METRICS = ["l_max_kg_per_m", "s_event_max_kg_per_m", "s_window_1h_kg_per_m", "total_shed_kg_per_m"]


def panel(c: Constructability) -> list[tuple[str, list]]:
    items = [("uniform", s) for s in uniform_constructable_segments(c)]
    rng = np.random.default_rng(9001)
    for mode in ("geometry", "surface", "joint"):
        for _ in range(20):
            items.append((mode, decode(rng.random(n_variables(mode, c)), mode, c)["segments"]))
    return items


def job(args):
    cfg, family, segs, dt, refine = args
    c = constructability_from_config(cfg)
    c = Constructability(**{**c.__dict__, "cells": c.cells * refine})
    scaled = [[n * refine, s, k] for n, s, k in segs]
    design = design_from_segments(scaled, c, family)
    sim = simulation_config(cfg)
    rows = []
    for w in weather_set_v2(cfg, dt):
        rec = evaluate_v2(design, [w], sim, EventSpec())
        rows.append(
            {
                "family": family,
                "segments": ";".join(f"{n}x{s}d{k}" for n, s, k in segs),
                "dt_h": dt,
                "cells": c.cells,
                "weather": w.name,
                **{
                    k: rec[k]
                    for k in [
                        *METRICS,
                        "event_count_max",
                        "mass_balance_abs_max",
                        "legacy_s_step_max_kg_per_m",
                    ]
                },
            }
        )
    return rows


def main() -> None:
    cfg = yaml.safe_load(open("config/production.yaml"))
    c = constructability_from_config(cfg)
    items = panel(c)
    jobs = [(cfg, f, s, dt, 1) for f, s in items for dt in (1.0, 0.5, 0.25, 0.125, 0.0625)]
    jobs += [(cfg, f, s, dt, r) for f, s in items for dt in (0.25,) for r in (2, 4)]
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(2) as pool:
        rows = [r for chunk in pool.imap_unordered(job, jobs, chunksize=4) for r in chunk]
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "convergence_runs.csv", index=False)
    summarize(df)


def summarize(df: pd.DataFrame) -> None:
    df = df.drop_duplicates(["segments", "weather", "dt_h", "cells"])
    key = ["segments", "weather"]
    ref = df[(df.dt_h == 0.0625) & (df.cells == 24)].set_index(key).sort_index()
    summary = []
    for (dt, cells), grp in df.groupby(["dt_h", "cells"]):
        g = grp.set_index(key).sort_index().reindex(ref.index)
        row = {"dt_h": dt, "cells": cells, "pairs": int(g[METRICS[0]].notna().sum())}
        for m in METRICS:
            x, r = g[m].to_numpy(), ref[m].to_numpy()
            diff = np.abs(x - r)
            ok = diff <= np.maximum(0.02 * np.abs(r), 1.0)
            row[f"{m}__agree_frac"] = float(ok.mean())
            with np.errstate(divide="ignore", invalid="ignore"):
                rel = np.where(np.abs(r) > 0, diff / np.abs(r), np.nan)
            row[f"{m}__median_rel"] = float(np.nanmedian(rel))
            row[f"{m}__p95_rel"] = float(np.nanpercentile(rel, 95))
            row[f"{m}__max_abs"] = float(diff.max())
        ec = np.abs(g.event_count_max.to_numpy() - ref.event_count_max.to_numpy())
        row["event_count_within1_frac"] = float((ec <= 1).mean())
        row["mass_balance_max"] = float(g.mass_balance_abs_max.max())
        row["acceptable"] = bool(
            all(row[f"{m}__agree_frac"] >= 0.95 for m in METRICS)
            and row["event_count_within1_frac"] >= 0.9
            and row["mass_balance_max"] < 1e-6
        )
        summary.append(row)
    s = pd.DataFrame(summary)
    s.to_csv(OUT / "convergence_summary.csv", index=False)
    print(s.T.to_string())
    ok = s[(s.cells == 24) & (s.acceptable) & (s.dt_h > 0.0625)]
    choice = float(ok.dt_h.max()) if len(ok) else 0.0625
    (OUT / "production_dt_choice.json").write_text(json.dumps({"production_dt_h": choice}, indent=2))
    print("production dt", choice)


if __name__ == "__main__":
    import sys

    if "--summary" in sys.argv:
        summarize(pd.read_csv(OUT / "convergence_runs.csv"))
    else:
        main()
