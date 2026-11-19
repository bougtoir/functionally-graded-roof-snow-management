"""Reviewer-driven supplementary analyses (R1).

1. Robustness factor attribution: Spearman rank correlation of each design's sampled outcomes
   with the five uncertainty factors, and drivers of release jumps above 10x nominal.
2. Roof-length sensitivity: the constructable uniform set and every nondominated design are
   re-evaluated (not re-optimised) at 4, 8 and 12 m with 24 cells.
3. Search budgets: evaluations and runtime per search.
4. Uniform threshold check: designs whose largest event equals their retained maximum.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

from graded_roof.metrics import nondominated_mask
from graded_roof.optimization_v2 import evaluate_many
from graded_roof.simulation_v2 import EventSpec
from graded_roof.study import simulation_config

R = Path("results/r1")
OUT = R / "review"
OBJ = ["l_max_kg_per_m", "s_event_max_kg_per_m"]
FACT = [
    "friction_factor",
    "adhesion_factor",
    "density_factor",
    "snowfall_factor",
    "temperature_offset_c",
]
LENGTHS = (4.0, 8.0, 12.0)


def factor_attribution() -> None:
    s = pd.read_csv(R / "robustness/uncertainty_samples.csv")
    cls = pd.read_csv(R / "robustness/robustness_classified.csv")[["segments", "class", *OBJ]]
    cls = cls.rename(columns={OBJ[0]: "l_nom", OBJ[1]: "s_nom"})
    runs = (
        pd.read_csv(R / "robustness/robustness_runs.csv")
        .merge(s, on="sample")
        .merge(cls, on="segments")
    )
    rows = []
    for (k, seg), g in runs.groupby(["class", "segments"]):
        for o in OBJ:
            for f in FACT:
                rho = spearmanr(g[f], g[o]).statistic if g[o].nunique() > 1 else np.nan
                rows.append({"class": k, "segments": seg, "objective": o, "factor": f, "rho": rho})
    per = pd.DataFrame(rows)
    per.to_csv(OUT / "factor_rank_correlation_per_design.csv", index=False)
    summ = (
        per.groupby(["class", "objective", "factor"])
        .rho.agg(
            designs="size",
            median_rho="median",
            q25=lambda x: np.nanpercentile(x, 25) if x.notna().any() else np.nan,
            q75=lambda x: np.nanpercentile(x, 75) if x.notna().any() else np.nan,
            frac_abs_gt_0_3=lambda x: float((x.abs() > 0.3).mean()),
        )
        .reset_index()
    )
    summ.to_csv(OUT / "factor_rank_correlation_summary.csv", index=False)
    gi = runs[runs["class"] == "graded_intermediate"].copy()
    gi["jump"] = gi[OBJ[1]] > 10 * np.maximum(gi.s_nom, 1.0)
    drv = gi.groupby("jump")[FACT].median().T
    drv.columns = ["no_jump_median", "jump_median"]
    drv["jump_fraction"] = gi.jump.mean()
    drv["n_samples"] = len(gi)
    drv.rename_axis("factor").reset_index().to_csv(OUT / "release_jump_drivers.csv", index=False)
    print(
        summ[summ["class"].isin(["graded_intermediate", "uniform_shedding"])].round(3).to_string()
    )
    print(drv.round(3).to_string())


def _gap(df: pd.DataFrame, uni: set[str]) -> dict:
    df = df.drop_duplicates("segments").set_index("segments")
    u = df.loc[sorted(uni), OBJ].drop_duplicates()
    u = u[nondominated_mask(u.to_numpy())]
    a = df[nondominated_mask(df[OBJ].to_numpy())].copy()
    a["graded"] = a.index.str.contains(";")
    pairs = a.groupby(OBJ).graded.min().reset_index()
    L = np.sort(u[OBJ[0]].to_numpy())
    k = int(np.diff(L).argmax())
    lo, hi = L[k], L[k + 1]
    inner = pairs[(pairs[OBJ[0]] > lo * (1 + 1e-9)) & (pairs[OBJ[0]] < hi * (1 - 1e-9))]
    return {
        "uniform_front_pairs": len(u),
        "combined_front_pairs": len(pairs),
        "uniform_gap_lo": lo,
        "uniform_gap_hi": hi,
        "pairs_in_uniform_gap": len(inner),
        "graded_pairs_in_gap": int(inner.graded.sum()),
        "gap_s_event_min": inner[OBJ[1]].min() if len(inner) else np.nan,
        "gap_s_event_max": inner[OBJ[1]].max() if len(inner) else np.nan,
    }


def roof_length(cfg: dict) -> None:
    sys.path.insert(0, "scripts")
    from r1_analyze import parse

    uni = set(pd.read_csv(R / "optimization/uniform_constructable_evaluated.csv").segments)
    fr = set(pd.read_csv(R / "robustness/robustness_classified.csv").segments)
    keys = sorted(uni | fr)
    sim, spec = simulation_config(cfg), EventSpec()
    rows, allev = [], []
    for length in LENGTHS:
        c = json.loads(json.dumps(cfg))
        c["roof"]["length_m"] = length
        ev = evaluate_many(c, [parse(k) for k in keys], dt_hours=1.0, sim=sim, spec=spec)
        ev["roof_length_m"] = length
        allev.append(ev)
        rows.append({"roof_length_m": length, "designs": len(keys), **_gap(ev, uni)})
    pd.concat(allev).to_csv(OUT / "roof_length_runs.csv", index=False)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "roof_length_sensitivity.csv", index=False)
    print(df.round(2).to_string())


def budgets() -> None:
    d = pd.read_csv(R / "pareto/run_diagnostics.csv")
    b = d.groupby("mode").agg(
        seeds=("seed", "nunique"),
        objective_evaluations=("objective_evaluations", "sum"),
        unique_designs_simulated=("unique_designs_simulated", "sum"),
        runtime_s_total=("runtime_s", "sum"),
        runtime_s_per_seed_median=("runtime_s", "median"),
        feasible_fraction=("feasible_fraction", "min"),
    )
    u = pd.read_csv(R / "optimization/uniform_constructable_evaluated.csv")
    g = pd.read_csv(R / "optimization/uniform_continuous_grid_evaluated.csv")
    extra = pd.DataFrame(
        {
            "seeds": [0, 0],
            "objective_evaluations": [len(u), len(g)],
            "unique_designs_simulated": [
                u.segments.nunique() if "segments" in u else len(u),
                len(g),
            ],
        },
        index=["uniform_exhaustive", "uniform_continuous_grid"],
    )
    pd.concat([b, extra]).rename_axis("search").reset_index().to_csv(
        OUT / "search_budgets.csv", index=False
    )
    print(pd.concat([b, extra]).round(1).to_string())


def uniform_threshold() -> None:
    u = pd.read_csv(R / "optimization/uniform_constructable_evaluated.csv").drop_duplicates(
        "segments"
    )
    u["slope_deg"] = u.segments.str.extract(r"x(\d+)d").astype(int)
    u["surface_class"] = u.segments.str.extract(r"d(\d+)$").astype(int)
    shed = u[u[OBJ[0]] < u[OBJ[0]].max() - 1e-6]
    shed = shed.assign(release_equals_retained=np.isclose(shed[OBJ[0]], shed[OBJ[1]], rtol=1e-6))
    shed.to_csv(OUT / "uniform_threshold_check.csv", index=False)
    print(shed.groupby("release_equals_retained").slope_deg.agg(["size", "min", "max"]))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load(open("config/production.yaml"))
    budgets()
    uniform_threshold()
    factor_attribution()
    if "--skip-length" not in sys.argv:
        roof_length(cfg)
