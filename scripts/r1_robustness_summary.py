"""Classify robustness results and compare designs in Q95 objective space."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from graded_roof.metrics import nondominated_mask  # noqa: E402

P, R = Path("results/r1/pareto"), Path("results/r1/robustness")
O = ["l_max_kg_per_m", "s_event_max_kg_per_m"]  # noqa: E741

if __name__ == "__main__":
    gap = pd.read_csv(P / "uniform_gap_coverage.csv")
    lo, hi = gap.uniform_gap_lo[0], gap.uniform_gap_hi[0]
    names = ("uniform", "geometry", "surface", "joint", "combined")
    nom = pd.concat([pd.read_csv(P / f"front_{n}.csv") for n in names])
    nom = nom.drop_duplicates("segments").set_index("segments")[O]
    s = pd.read_csv(R / "robustness_summary.csv").set_index("segments").join(nom)
    graded = s.index.str.contains(";")
    s["class"] = np.select(
        [~graded & (s[O[0]] >= hi - 1e-6), ~graded, (s[O[0]] > lo) & (s[O[0]] < hi)],
        ["uniform_retention", "uniform_shedding", "graded_intermediate"],
        "graded_other",
    )
    runs = pd.read_csv(R / "robustness_runs.csv").join(s["class"], on="segments")
    s["frac_samples_s_above_uniform_gap_lo"] = (
        runs.assign(b=runs[O[1]] > lo).groupby("segments").b.mean()
    )
    s["on_q95_front"] = nondominated_mask(s[["l_q", "s_q"]].to_numpy())
    s.reset_index().to_csv(R / "robustness_classified.csv", index=False)
    agg = s.groupby("class").agg(
        designs=("s_q", "size"),
        nominal_s_min=(O[1], "min"),
        nominal_s_max=(O[1], "max"),
        q95_s_min=("s_q", "min"),
        q95_s_median=("s_q", "median"),
        q95_s_max=("s_q", "max"),
        q95_l_min=("l_q", "min"),
        q95_l_max=("l_q", "max"),
        frac_above_lo_median=("frac_samples_s_above_uniform_gap_lo", "median"),
        on_q95_front=("on_q95_front", "sum"),
    )
    agg["uniform_gap_lo"] = lo
    agg["max_mass_balance_error"] = s.mass_balance_max.max()
    agg.reset_index().to_csv(R / "robustness_class_summary.csv", index=False)
    print(agg.round(3).to_string())
    print(s[s.on_q95_front].sort_values("l_q")[["l_q", "s_q", "class"]].round(1).to_string())
