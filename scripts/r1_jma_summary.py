"""Per station-winter comparison of uniform and graded designs under JMA forcing."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from graded_roof.metrics import nondominated_mask  # noqa: E402

O = ["l_max_kg_per_m", "s_event_max_kg_per_m"]  # noqa: E741
P, J = Path("results/r1/pareto"), Path("results/r1/jma")

if __name__ == "__main__":
    j = pd.read_csv(J / "jma_runs.csv")
    g = pd.read_csv(P / "uniform_gap_coverage.csv")
    lo, hi = g.uniform_gap_lo[0], g.uniform_gap_hi[0]
    fc = pd.read_csv(P / "front_combined.csv")
    tol = 1e-6 * hi
    inter = set(fc[(fc[O[0]] > lo + tol) & (fc[O[0]] < hi - tol)].segments)
    graded = j.segments.str.contains(";")
    j["class"] = np.select(
        [~graded, j.segments.isin(inter)], ["uniform", "graded_intermediate"], "graded_other"
    )
    rows = []
    for sw, gg in j.groupby("station_winter"):
        u = gg[gg["class"] == "uniform"]
        un = u[nondominated_mask(u[O].to_numpy())][O].drop_duplicates()
        a = gg[nondominated_mask(gg[O].to_numpy())]
        L = np.sort(un[O[0]].unique())
        k = int(np.diff(L).argmax())
        lo_s, hi_s = L[k], L[k + 1]
        t = 1e-6 * hi_s
        ing = a[(a["class"] != "uniform") & (a[O[0]] > lo_s + t) & (a[O[0]] < hi_s - t)]
        gi = gg[gg["class"] == "graded_intermediate"]
        rows.append(
            {
                "station_winter": sw,
                "uniform_front_pairs": len(un),
                "uniform_gap_lo": lo_s,
                "uniform_gap_hi": hi_s,
                "graded_pairs_in_gap": len(ing[O].drop_duplicates()),
                "gap_s_event_min": ing[O[1]].min(),
                "gap_s_event_max": ing[O[1]].max(),
                "nominal_intermediate_s_event_median": gi[O[1]].median(),
                "nominal_intermediate_l_max_median": gi[O[0]].median(),
                "max_mass_balance_error": gg.mass_balance_abs.max(),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(J / "jma_station_summary.csv", index=False)
    print(df.round(1).to_string())
