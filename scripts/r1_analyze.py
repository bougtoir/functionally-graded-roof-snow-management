"""R1 Pareto reliability analysis of constructability-constrained optimisation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from graded_roof.metrics import (
    additive_epsilon_indicator,
    matched_objective_improvement,
    nondominated_mask,
    normalized_hypervolume_2d,
)
from graded_roof.optimization_v2 import evaluate_many
from graded_roof.simulation_v2 import EventSpec
from graded_roof.study import simulation_config

OPT = Path("results/r1/optimization")
OUT = Path("results/r1/pareto")
OBJ = ["l_max_kg_per_m", "s_event_max_kg_per_m"]
MODES = ["geometry", "surface", "joint"]
GENS = (15, 30, 45)


def front(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates("segments")
    pts = df[OBJ].to_numpy()
    return df[nondominated_mask(pts)].sort_values(OBJ[0])


def parse(key: str) -> list[list[int]]:
    out = []
    for tok in key.split(";"):
        n, rest = tok.split("x")
        s, k = rest.split("d")
        out.append([int(n), int(s), int(k)])
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load(open("config/production.yaml"))
    uni = pd.read_csv(OPT / "uniform_constructable_evaluated.csv").assign(mode="uniform", seed=0)
    runs, metas = [], []
    for meta_path in sorted(OPT.glob("*_meta.json")):
        meta = json.loads(meta_path.read_text())
        stem = f"{meta['mode']}_seed_{meta['seed']}"
        ev = pd.read_csv(OPT / f"{stem}_evaluated.csv")
        hist = pd.read_csv(OPT / f"{stem}_history.csv")
        first = hist.groupby("segments").generation.min().rename("first_generation")
        ev = ev.merge(first, left_on="segments", right_index=True, how="left")
        runs.append(ev.assign(mode=meta["mode"], seed=meta["seed"]))
        metas.append(meta)
    allev = pd.concat([uni, *runs], ignore_index=True)
    allev.to_csv(OUT / "all_evaluated_designs.csv", index=False)
    ref_base = allev[OBJ].max().to_numpy()
    refs = {"max_x1.1": 1.1 * ref_base, "max_x1.05": 1.05 * ref_base, "max_x1.5": 1.5 * ref_base}
    uni_front = front(uni)
    combined = front(allev)
    fronts = {"uniform": uni_front}
    rows = []
    for mode in MODES:
        mode_ev = allev[allev["mode"] == mode]
        if mode_ev.empty:
            continue
        fronts[mode] = front(pd.concat([mode_ev, uni]))
        for seed, run in mode_ev.groupby("seed"):
            for g in GENS:
                sub = run[run.first_generation <= g]
                f = front(sub)
                row = {
                    "mode": mode,
                    "seed": seed,
                    "generation": g,
                    "front_size": len(f),
                    "evaluated_unique": len(sub),
                }
                for name, r in refs.items():
                    row[f"hv_{name}"] = normalized_hypervolume_2d(f[OBJ].to_numpy(), tuple(r))
                row["eps_to_combined"] = additive_epsilon_indicator(
                    f[OBJ].to_numpy(), combined[OBJ].to_numpy()
                )
                rows.append(row)
    per_seed = pd.DataFrame(rows)
    per_seed.to_csv(OUT / "per_seed_budget_hypervolume.csv", index=False)
    summ = []
    for name, f in fronts.items():
        pts = f[OBJ].to_numpy()
        row = {"set": name, "front_size": len(f)}
        for rn, r in refs.items():
            row[f"hv_{rn}"] = normalized_hypervolume_2d(pts, tuple(r))
        row["eps_set_to_uniform"] = additive_epsilon_indicator(pts, uni_front[OBJ].to_numpy())
        row["eps_uniform_to_set"] = additive_epsilon_indicator(uni_front[OBJ].to_numpy(), pts)
        row.update(matched_objective_improvement(pts, uni_front[OBJ].to_numpy()))
        row["graded_points_on_front"] = int((~f.segments.str.count(";").eq(0)).sum())
        summ.append(row)
        f.to_csv(OUT / f"front_{name}.csv", index=False)
    pd.DataFrame(summ).to_csv(OUT / "front_summary.csv", index=False)
    pd.DataFrame(metas).to_csv(OUT / "run_diagnostics.csv", index=False)
    combined.to_csv(OUT / "front_combined.csv", index=False)
    # pre-specified fine re-check of all nondominated designs
    keys = sorted(set(pd.concat(list(fronts.values())).segments))
    sim, spec = simulation_config(cfg), EventSpec()
    fine = evaluate_many(cfg, [parse(k) for k in keys], dt_hours=0.0625, sim=sim, spec=spec)
    cfg48 = json.loads(json.dumps(cfg))
    cfg48["roof"]["cells"] = 2 * cfg["roof"]["cells"]
    cfg48["roof"]["minimum_segment_cells"] = 2 * cfg["roof"]["minimum_segment_cells"]
    fine48 = evaluate_many(
        cfg48,
        [[[2 * n, s, k] for n, s, k in parse(k)] for k in keys],
        dt_hours=0.25,
        sim=sim,
        spec=spec,
    )
    base = allev.drop_duplicates("segments").set_index("segments").loc[keys, OBJ]
    chk = pd.DataFrame({"segments": keys})
    for o in OBJ:
        chk[f"{o}__dt1"] = base[o].to_numpy()
        chk[f"{o}__dt0.0625"] = fine[o].to_numpy()
        chk[f"{o}__N48"] = fine48[o].to_numpy()
    chk.to_csv(OUT / "front_recheck_fine.csv", index=False)
    fine_fronts = {}
    for name, f in fronts.items():
        pts = chk.set_index("segments").loc[f.segments, [f"{o}__dt0.0625" for o in OBJ]].to_numpy()
        fine_fronts[name] = pts[nondominated_mask(pts)]
    rr = []
    uf = fine_fronts["uniform"]
    for name, pts in fine_fronts.items():
        hv = normalized_hypervolume_2d(pts, tuple(refs["max_x1.1"]))
        rr.append(
            {
                "set": name,
                "hv_max_x1.1_fine": hv,
                "eps_set_to_uniform_fine": additive_epsilon_indicator(pts, uf),
                "eps_uniform_to_set_fine": additive_epsilon_indicator(uf, pts),
            }
        )
    pd.DataFrame(rr).to_csv(OUT / "front_summary_fine_recheck.csv", index=False)
    print(pd.DataFrame(summ).round(4).T.to_string())
    print(pd.DataFrame(rr).round(4).to_string())


if __name__ == "__main__":
    main()
