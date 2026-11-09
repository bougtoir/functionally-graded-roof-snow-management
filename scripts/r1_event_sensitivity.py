"""R1 sensitivity of the frontier comparison to event-definition and entrainment choices."""

from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from graded_roof.metrics import additive_epsilon_indicator, nondominated_mask
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
OUT = Path("results/r1/event_sensitivity")
VARIANTS = {
    "base": (EventSpec(), True),
    "tau_sep_10min": (EventSpec(separation_h=1.0 / 6.0), True),
    "tau_sep_3h": (EventSpec(separation_h=3.0), True),
    "q_min_0.1": (EventSpec(flow_threshold_kg_m_h=0.1), True),
    "q_min_10": (EventSpec(flow_threshold_kg_m_h=10.0), True),
    "no_entrainment": (EventSpec(), False),
}
_W: dict = {}


def _init(cfg, dt):
    _W.update(
        c=constructability_from_config(cfg), sim=simulation_config(cfg), ws=weather_set_v2(cfg, dt)
    )


def _job(args):
    key, segs, name = args
    spec, ent = VARIANTS[name]
    d = design_from_segments(segs, _W["c"], key)
    res = [simulate_v2(d, w, _W["sim"], spec, entrainment=ent) for w in _W["ws"]]
    return {
        "segments": key,
        "variant": name,
        "l_max_kg_per_m": max(r.l_max_kg_per_m for r in res),
        "s_event_max_kg_per_m": max(r.s_event_max_kg_per_m for r in res),
    }


def summarize(out: pd.DataFrame, uni_keys: list[str]) -> pd.DataFrame:
    """Per variant: unique objective pairs on the uniform and combined fronts and gap coverage."""
    obj = ["l_max_kg_per_m", "s_event_max_kg_per_m"]
    rows = []
    for v, g in out.groupby("variant"):
        g = g.drop_duplicates("segments").set_index("segments")
        g["graded"] = g.index.str.contains(";")
        u = g.loc[uni_keys, obj].drop_duplicates()
        u = u[nondominated_mask(u.to_numpy())]
        a = g[nondominated_mask(g[obj].to_numpy())]
        pairs = a.groupby(obj).graded.min().reset_index()
        L = np.sort(u[obj[0]].to_numpy())
        k = int(np.diff(L).argmax())
        lo, hi = L[k], L[k + 1]
        tol = 1e-6 * hi
        inner = pairs[(pairs[obj[0]] > lo + tol) & (pairs[obj[0]] < hi - tol)]
        rows.append(
            {
                "variant": v,
                "uniform_front_pairs": len(u),
                "combined_front_pairs": len(pairs),
                "graded_only_pairs_on_combined_front": int(pairs.graded.sum()),
                "eps_uniform_to_combined": additive_epsilon_indicator(
                    u.to_numpy(), pairs[obj].to_numpy()
                ),
                "uniform_gap_lo": lo,
                "uniform_gap_hi": hi,
                "pairs_in_uniform_gap": len(inner),
                "gap_s_event_min": inner[obj[1]].min() if len(inner) else np.nan,
                "gap_s_event_max": inner[obj[1]].max() if len(inner) else np.nan,
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "event_sensitivity_summary.csv", index=False)
    print(df.round(2).to_string())
    return df


if __name__ == "__main__":
    sys.path.insert(0, "scripts")
    from r1_analyze import parse

    cfg = yaml.safe_load(open("config/production.yaml"))
    dt = json.loads(Path("results/r1/convergence/production_dt_choice.json").read_text())[
        "production_dt_h"
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    allev = pd.read_csv(PARETO / "all_evaluated_designs.csv").drop_duplicates("segments")
    uni_keys = allev[allev["mode"] == "uniform"].segments.tolist()
    front_keys = set(pd.concat([pd.read_csv(f) for f in FRONT_FILES]).segments)
    keys = sorted(set(uni_keys) | front_keys)
    if "--summary" in sys.argv:
        summarize(pd.read_csv(OUT / "event_sensitivity_runs.csv"), uni_keys)
        raise SystemExit
    jobs = [(k, parse(k), v) for k in keys for v in VARIANTS]
    with Pool(2, initializer=_init, initargs=(cfg, dt)) as pool:
        out = pd.DataFrame(pool.map(_job, jobs, chunksize=10))
    out.to_csv(OUT / "event_sensitivity_runs.csv", index=False)
    summarize(out, uni_keys)
