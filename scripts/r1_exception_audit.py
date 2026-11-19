"""Numerical-exception impact audit (R1 final pass).

Lists every dt = 1 h design-winter pair outside the pre-specified tolerance against the
dt = 0.0625 h, 24-cell reference, maps the failing designs onto the fronts, and recomputes the
uniform gap and the graded pairs inside it entirely from fine-resolution objectives.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from graded_roof.metrics import nondominated_mask

R = Path("results/r1")
OUT = R / "review"
MET = ["l_max_kg_per_m", "s_event_max_kg_per_m", "s_window_1h_kg_per_m", "total_shed_kg_per_m"]
OBJ = MET[:2]


def gap_pairs(uni: pd.DataFrame, grad: pd.DataFrame) -> dict:
    u = uni[OBJ].drop_duplicates()
    u = u[nondominated_mask(u.to_numpy())]
    L = np.sort(u[OBJ[0]].to_numpy())
    k = int(np.diff(L).argmax())
    lo, hi = L[k], L[k + 1]
    allp = pd.concat([uni.assign(graded=False), grad.assign(graded=True)])
    a = allp[nondominated_mask(allp[OBJ].to_numpy())]
    pairs = a.groupby(OBJ).graded.min().reset_index()
    inner = pairs[(pairs[OBJ[0]] > lo * (1 + 1e-9)) & (pairs[OBJ[0]] < hi * (1 - 1e-9))]
    keys = set(a[a.graded & a[OBJ[0]].between(lo * (1 + 1e-9), hi * (1 - 1e-9))].segments)
    return {
        "uniform_front_pairs": len(u),
        "uniform_gap_lo": lo,
        "uniform_gap_hi": hi,
        "graded_pairs_in_gap": int(inner.graded.sum()),
        "gap_s_event_min": inner[OBJ[1]].min(),
        "gap_s_event_max": inner[OBJ[1]].max(),
        "_keys": keys,
    }


def main() -> None:
    cfg = yaml.safe_load(open("config/production.yaml"))
    runs = pd.read_csv(R / "convergence/convergence_runs.csv").drop_duplicates(
        ["segments", "weather", "dt_h", "cells"]
    )
    print(runs.groupby(["family", "dt_h", "cells"]).size().to_string())
    ref = runs[(runs.dt_h == 0.0625) & (runs.cells == 24)].set_index(["segments", "weather"])
    tst = runs[(runs.dt_h == 1.0) & (runs.cells == 24)].set_index(["segments", "weather"])
    m = tst.join(ref, rsuffix="__ref", how="inner")
    classes = list(cfg["surface"]["discrete_classes"].values())
    g = 9.80665
    rows = []
    fu = set(pd.read_csv(R / "pareto/front_uniform.csv").segments)
    fc = pd.read_csv(R / "pareto/front_combined.csv")
    lo0, hi0 = (
        pd.read_csv(R / "pareto/uniform_gap_coverage.csv")
        .set_index("set")
        .loc["combined", ["uniform_gap_lo", "uniform_gap_hi"]]
    )
    gapk = set(
        fc[
            (fc.segments.str.contains(";")) & fc[OBJ[0]].between(lo0 * (1 + 1e-9), hi0 * (1 - 1e-9))
        ].segments
    )
    for (seg, w), r in m.iterrows():
        for met in MET:
            a, b = r[met], r[f"{met}__ref"]
            tol = max(0.02 * abs(b), 1.0)
            if abs(a - b) > tol:
                thr = np.nan
                if ";" not in seg:
                    sl, k = int(seg.split("x")[1].split("d")[0]), int(seg.split("d")[1])
                    th = np.deg2rad(sl)
                    c = classes[k]
                    den = g * (np.sin(th) - c["mu_static"] * np.cos(th))
                    thr = c["adhesion_pa"] / den if den > 0 else np.inf
                rows.append(
                    {
                        "segments": seg,
                        "family": r["family"],
                        "weather": w,
                        "metric": met,
                        "dt1": a,
                        "ref_dt0.0625": b,
                        "abs_diff": abs(a - b),
                        "tolerance": tol,
                        "rel_diff": abs(a - b) / max(abs(b), 1.0),
                        "events_dt1": r["event_count_max"],
                        "events_ref": r["event_count_max__ref"],
                        "event_split_or_merge": r["event_count_max"] != r["event_count_max__ref"],
                        "static_threshold_mass_kg_m2": thr,
                        "on_uniform_front": seg in fu,
                        "on_combined_front": seg in set(fc.segments),
                        "graded_in_uniform_gap": seg in gapk,
                    }
                )
    fail = pd.DataFrame(rows)
    fail.to_csv(OUT / "exception_failed_cases.csv", index=False)
    # design-level (worst case over winters), fine-resolution front reconstruction
    uni_f = (
        runs[(runs.family == "uniform") & (runs.dt_h == 0.0625) & (runs.cells == 24)]
        .groupby("segments")[OBJ]
        .max()
        .reset_index()
    )
    rc = pd.read_csv(R / "pareto/front_recheck_fine.csv")
    grad_f = rc[rc.segments.str.contains(";")].rename(columns={f"{o}__dt0.0625": o for o in OBJ})[
        ["segments", *OBJ]
    ]
    uni_1 = pd.read_csv(R / "optimization/uniform_constructable_evaluated.csv").drop_duplicates(
        "segments"
    )[["segments", *OBJ]]
    grad_1 = rc[rc.segments.str.contains(";")].rename(columns={f"{o}__dt1": o for o in OBJ})[
        ["segments", *OBJ]
    ]
    base, fine = gap_pairs(uni_1, grad_1), gap_pairs(uni_f, grad_f)
    seeds = []
    for p in sorted((R / "optimization").glob("*_seed_*_evaluated.csv")):
        ev = set(pd.read_csv(p, usecols=["segments"]).segments)
        seeds.append(
            {
                "run": p.stem.replace("_evaluated", ""),
                "fine_gap_designs_found": len(ev & fine["_keys"]),
            }
        )
    sd = pd.DataFrame(seeds)
    summ = {
        "pairs_compared": int(len(m)),
        "pairs_failing_any_metric": int(fail.drop_duplicates(["segments", "weather"]).shape[0])
        if len(fail)
        else 0,
        "failures_by_metric": fail.metric.value_counts().to_dict() if len(fail) else {},
        "failures_by_family": fail.drop_duplicates(["segments", "weather"])
        .family.value_counts()
        .to_dict()
        if len(fail)
        else {},
        "failing_designs_on_uniform_front": int(fail[fail.on_uniform_front].segments.nunique())
        if len(fail)
        else 0,
        "failing_designs_on_combined_front": int(fail[fail.on_combined_front].segments.nunique())
        if len(fail)
        else 0,
        "failing_designs_graded_in_gap": int(fail[fail.graded_in_uniform_gap].segments.nunique())
        if len(fail)
        else 0,
        "gap_dt1": {k: v for k, v in base.items() if k != "_keys"},
        "gap_fine_dt0.0625": {k: v for k, v in fine.items() if k != "_keys"},
        "runs_finding_fine_gap_designs": f"{int((sd.fine_gap_designs_found > 0).sum())}/{len(sd)}",
        "fine_gap_designs_per_run_min_max": [
            int(sd.fine_gap_designs_found.min()),
            int(sd.fine_gap_designs_found.max()),
        ],
    }
    sd.to_csv(OUT / "exception_fine_gap_per_run.csv", index=False)
    (OUT / "exception_summary.json").write_text(json.dumps(summ, indent=2, default=float))
    print(json.dumps(summ, indent=2, default=float))
    if len(fail):
        print(fail.sort_values("abs_diff", ascending=False).head(12).round(2).to_string())


if __name__ == "__main__":
    main()
