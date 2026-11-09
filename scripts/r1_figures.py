"""R1 figures, generated only from canonical machine-readable outputs in results/r1/."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from graded_roof.forcing_v2 import continuous_synthetic_weather  # noqa: E402
from graded_roof.optimization_v2 import (  # noqa: E402
    constructability_from_config,
    design_from_segments,
)
from graded_roof.simulation_v2 import EventSpec, simulate_v2  # noqa: E402
from graded_roof.study import simulation_config  # noqa: E402

R = Path("results/r1")
FIG = Path("figures/r1")
DATA = R / "figure_data"
O = ["l_max_kg_per_m", "s_event_max_kg_per_m"]  # noqa: E741
COL = {"uniform": "#222222", "geometry": "#1b9e77", "surface": "#d95f02", "joint": "#7570b3"}
CLASS_COL = ["#9ecae1", "#fdae6b", "#a1d99b"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.linewidth": 0.6})


def tiff_rgb(path: Path) -> None:
    """Flatten the alpha channel onto white; journals expect RGB TIFF."""
    from PIL import Image

    im = Image.open(path)
    if im.mode != "RGB":
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.getchannel("A") if "A" in im.mode else None)
        bg.save(path, compression="tiff_lzw", dpi=(1000, 1000))


def save(fig, name: str, data: pd.DataFrame) -> None:
    for sub in ("png", "tiff", "vector"):
        (FIG / sub).mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "png" / f"{name}.png", dpi=1000, bbox_inches="tight")
    fig.savefig(
        FIG / "tiff" / f"{name}.tiff",
        dpi=1000,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    tiff_rgb(FIG / "tiff" / f"{name}.tiff")
    fig.savefig(FIG / "vector" / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / "vector" / f"{name}.svg", bbox_inches="tight")
    DATA.mkdir(parents=True, exist_ok=True)
    data.to_csv(DATA / f"{name}.csv", index=False)
    plt.close(fig)


def parse(key):
    sys.path.insert(0, "scripts")
    from r1_analyze import parse as p

    return p(key)


def fig1(cfg):
    c = constructability_from_config(cfg)
    key = pd.read_csv(R / "pareto/front_combined.csv").query(
        "segments.str.contains(';')", engine="python"
    )
    key = key.iloc[len(key) // 2].segments
    d = design_from_segments(parse(key), c, key)
    w = continuous_synthetic_weather(
        cfg["synthetic_weather"]["scenarios"][1],
        duration_h=cfg["synthetic_weather"]["duration_h"],
        dt_hours=1.0,
    )
    r = simulate_v2(d, w, simulation_config(cfg), EventSpec())
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.6), gridspec_kw={"width_ratios": [1, 1.4]})
    x = np.linspace(0, c.length_m, c.cells + 1)
    z = np.concatenate([[0], np.cumsum(-np.tan(np.deg2rad(d.slope_deg)) * np.diff(x))])
    klass = [int(s.split("d")[1]) for s in key.split(";") for _ in range(int(s.split("x")[0]))]
    for i in range(c.cells):
        ax[0].plot(
            x[i : i + 2], z[i : i + 2], color=CLASS_COL[klass[i]], lw=4, solid_capstyle="butt"
        )
    ax[0].set(
        xlabel="Distance from ridge (m)",
        ylabel="Elevation (m)",
        title="(a) Constructable graded profile",
    )
    for k, (name, *_rest) in enumerate(c.classes):
        ax[0].plot([], [], color=CLASS_COL[k], lw=4, label=name.replace("_", " "))
    ax[0].legend(frameon=False, fontsize=6, loc="lower left")
    t = np.arange(len(r.shed_per_step)) * w.dt_hours
    ax[1].bar(t, r.shed_per_step, width=w.dt_hours, color="0.5", label="Outflow per 1-h step")
    for e in r.events:
        ax[1].axvspan(e["start_h"], max(e["end_h"], e["start_h"] + 1), color="#e41a1c", alpha=0.15)
    ax[1].set(
        xlabel="Time (h)", ylabel="Eave outflow (kg m$^{-1}$)", title="(b) Physical events (shaded)"
    )
    ax[1].legend(frameon=False, fontsize=6)
    ev = pd.DataFrame(r.events)
    ev["segments"] = key
    save(fig, "figure_1_model_and_events", ev)


def fig2(cfg):
    rows = []
    fig, ax = plt.subplots(2, 1, figsize=(7.2, 3.6), sharex=True)
    for s in cfg["synthetic_weather"]["scenarios"]:
        w = continuous_synthetic_weather(
            s, duration_h=cfg["synthetic_weather"]["duration_h"], dt_hours=1.0
        )
        t = np.arange(len(w.temperature_c))
        ax[0].plot(t, w.snowfall_kg_m2, lw=0.8, label=s["name"].replace("_", " "))
        ax[1].plot(t, w.temperature_c, lw=0.8)
        rows.append(
            pd.DataFrame(
                {
                    "scenario": s["name"],
                    "t_h": t,
                    "snowfall_kg_m2_h": w.snowfall_kg_m2,
                    "rain_mm_h": w.rain_mm,
                    "temperature_c": w.temperature_c,
                }
            )
        )
    ax[0].set(ylabel="Snowfall (kg m$^{-2}$ h$^{-1}$)")
    ax[0].legend(frameon=False, fontsize=6)
    ax[1].axhline(0, color="0.6", lw=0.5)
    ax[1].set(xlabel="Time (h)", ylabel="Air temperature (°C)")
    save(fig, "figure_2_synthetic_forcing", pd.concat(rows))


def fig3():
    df = pd.read_csv(R / "convergence/convergence_runs.csv").drop_duplicates(
        ["segments", "weather", "dt_h", "cells"]
    )
    s = pd.read_csv(R / "convergence/convergence_summary.csv")
    d24 = df[df.cells == 24]
    ref = d24[d24.dt_h == 0.0625].set_index(["segments", "weather"])
    rows = []
    for dt, g in d24.groupby("dt_h"):
        g = g.set_index(["segments", "weather"]).reindex(ref.index)
        for col, lab in (
            ("legacy_s_step_max_kg_per_m", "submitted per-step S$_{max}$"),
            ("s_event_max_kg_per_m", "S$_{event,max}$"),
            ("s_window_1h_kg_per_m", "S$_{1h,max}$"),
        ):
            r = ref[col].to_numpy()
            m = r > 1
            rows.append(
                {
                    "dt_h": dt,
                    "metric": lab,
                    "median_ratio": float(np.median(g[col].to_numpy()[m] / r[m])),
                }
            )
    rr = pd.DataFrame(rows)
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.6))
    for lab, g in rr.groupby("metric", sort=False):
        ax[0].plot(g.dt_h, g.median_ratio, marker="o", ms=3, label=lab)
    ax[0].set(
        xscale="log",
        xlabel="Timestep (h)",
        ylabel="Median ratio to dt = 0.0625 h",
        title="(a) Endpoint dependence on dt",
    )
    ax[0].legend(frameon=False, fontsize=6)
    t = s[s.cells == 24].sort_values("dt_h")
    for col, lab in (
        ("l_max_kg_per_m__agree_frac", "L$_{max}$"),
        ("s_event_max_kg_per_m__agree_frac", "S$_{event,max}$"),
        ("s_window_1h_kg_per_m__agree_frac", "S$_{1h,max}$"),
        ("total_shed_kg_per_m__agree_frac", "total shed"),
    ):
        ax[1].plot(t.dt_h, t[col], marker="o", ms=3, label=lab)
    ax[1].axhline(0.95, ls="--", color="0.5", lw=0.7)
    ax[1].set(
        xscale="log",
        xlabel="Timestep (h)",
        ylabel="Fraction within tolerance",
        title="(b) Pre-specified criterion",
    )
    ax[1].legend(frameon=False, fontsize=6)
    save(fig, "figure_3_timestep_convergence", rr.merge(t, on="dt_h", how="left"))


def fig4():
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0))
    rows = []
    for name in ("uniform", "geometry", "surface", "joint"):
        p = R / f"pareto/front_{name}.csv"
        if not p.exists():
            continue
        f = pd.read_csv(p)
        for a in ax:
            a.step(f[O[0]], f[O[1]], where="post", color=COL[name], lw=0.8, alpha=0.8)
            a.scatter(f[O[0]], f[O[1]], s=6, color=COL[name], label=name if a is ax[0] else None)
        rows.append(f.assign(set=name)[["set", "segments", *O]])
    ax[0].set(
        xscale="symlog",
        xlabel="L$_{max}$ (kg m$^{-1}$)",
        ylabel="S$_{event,max}$ (kg m$^{-1}$)",
        title="(a) Full range",
    )
    ax[0].legend(frameon=False, fontsize=6)
    ax[1].set(
        xlim=(80, 6600),
        ylim=(-5, 400),
        xscale="log",
        xlabel="L$_{max}$ (kg m$^{-1}$)",
        title="(b) Intermediate region",
    )
    save(fig, "figure_4_constructable_pareto_fronts", pd.concat(rows))


def fig5(cfg):
    c = constructability_from_config(cfg)
    f = pd.read_csv(R / "pareto/front_combined.csv")
    g = f[f.segments.str.contains(";") & (f[O[0]] > 100)].sort_values(O[0])
    pick = (
        g.iloc[np.unique(np.linspace(0, len(g) - 1, min(4, len(g))).astype(int))] if len(g) else g
    )
    fig, ax = plt.subplots(1, max(len(pick), 1), figsize=(7.2, 2.2), sharey=True, squeeze=False)
    rows = []
    for a, (_, r) in zip(ax[0], pick.iterrows(), strict=False):
        d = design_from_segments(parse(r.segments), c, r.segments)
        klass = [
            int(s.split("d")[1]) for s in r.segments.split(";") for _ in range(int(s.split("x")[0]))
        ]
        xc = (np.arange(c.cells) + 0.5) * c.length_m / c.cells
        a.bar(
            xc,
            d.slope_deg,
            width=c.length_m / c.cells,
            color=[CLASS_COL[k] for k in klass],
            edgecolor="0.3",
            lw=0.2,
        )
        a.set(title=f"L={r[O[0]]:.0f}, S={r[O[1]]:.0f}", xlabel="Distance from ridge (m)")
        rows.append(
            pd.DataFrame(
                {"segments": r.segments, "x_m": xc, "slope_deg": d.slope_deg, "class_index": klass}
            )
        )
    ax[0][0].set_ylabel("Slope (°)")
    save(fig, "figure_5_intermediate_profiles", pd.concat(rows) if rows else pd.DataFrame())


def fig6():
    p = pd.read_csv(R / "pareto/per_seed_budget_hypervolume.csv")
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for mode, g in p.groupby("mode"):
        for _, s in g.groupby("seed"):
            ax.plot(
                s.generation, s["hv_max_x1.1"], color=COL[mode], lw=0.6, alpha=0.6, marker="o", ms=2
            )
        ax.plot([], [], color=COL[mode], label=mode)
    u = pd.read_csv(R / "pareto/front_summary.csv").set_index("set").loc["uniform", "hv_max_x1.1"]
    ax.axhline(u, color=COL["uniform"], ls="--", lw=0.7, label="uniform (exhaustive)")
    ax.set(xlabel="Generations", ylabel="Normalised hypervolume")
    ax.legend(frameon=False, fontsize=6)
    save(fig, "figure_6_search_budget_hypervolume", p)


def fig7():
    s = pd.read_csv(R / "robustness/robustness_summary.csv")
    allev = pd.read_csv(R / "pareto/all_evaluated_designs.csv").drop_duplicates("segments")
    s = s.merge(allev[["segments", "mode", *O]], on="segments", how="left")
    s["family"] = np.where(s.segments.str.contains(";"), "graded", "uniform")
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.8))
    for fam, g in s.groupby("family"):
        col = COL["uniform"] if fam == "uniform" else COL["joint"]
        ax[0].scatter(g[O[0]], g.l_q, s=8, color=col, label=fam)
        ax[1].scatter(g[O[1]], g.s_q, s=8, color=col)
    for a, lab in zip(ax, ("L$_{max}$", "S$_{event,max}$"), strict=True):
        lim = [1, max(s.l_q.max(), s.s_q.max(), 10) * 1.2]
        a.plot(lim, lim, color="0.6", lw=0.5)
        a.set(
            xscale="symlog",
            yscale="symlog",
            xlabel=f"Nominal {lab} (kg m$^{{-1}}$)",
            ylabel=f"Q95 {lab} (kg m$^{{-1}}$)",
        )
    ax[0].legend(frameon=False, fontsize=6)
    save(fig, "figure_7_robustness_q95", s)


def fig8():
    j = pd.read_csv(R / "jma/jma_runs.csv")
    j["family"] = np.where(j.segments.str.contains(";"), "graded", "uniform")
    fig, ax = plt.subplots(3, 4, figsize=(7.2, 5.0), sharex=True, sharey=True)
    for a, (sw, g) in zip(ax.flat, j.groupby("station_winter"), strict=False):
        for fam, h in g.groupby("family"):
            a.scatter(
                h[O[0]],
                h[O[1]],
                s=3,
                color=COL["uniform"] if fam == "uniform" else COL["joint"],
                label=fam,
            )
        a.set_title(sw, fontsize=6)
        a.set(xscale="symlog", yscale="symlog")
    ax[0, 0].legend(frameon=False, fontsize=5)
    fig.supxlabel("L$_{max}$ (kg m$^{-1}$)")
    fig.supylabel("S$_{event,max}$ (kg m$^{-1}$)")
    save(fig, "figure_8_jma_station_winters", j)


if __name__ == "__main__":
    cfg = yaml.safe_load(open("config/production.yaml"))
    for f in (
        lambda: fig1(cfg),
        lambda: fig2(cfg),
        fig3,
        fig4,
        lambda: fig5(cfg),
        fig6,
        fig7,
        fig8,
    ):
        f()
