"""Point-by-point response letter and reviewer response matrix (R1).

Reviewer comments are reproduced verbatim from the decision letter supplied by the author
(private/reviewer_comments/*.txt); responses come from private/r1_response/responses.yaml, with
{placeholders} filled from canonical CSVs. Outputs are written to private/r1_response/ because
reviewer comments are confidential and the repository is public.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import docx
import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, "scripts")
from r1_build_manuscript import para  # noqa: E402

PRIV = Path("private")
OUT = PRIV / "r1_response"
R = Path("results/r1")
HEAD = re.compile(r"^(General comments|Comment ([A-Z]?\d+)(?: — .*)?)$")
SKIP = {"Abstract", "Introduction", "Methods", "Results", "Discussion", "Limitations", "Conclusion"}
COLUMNS = [
    "Reviewer",
    "Comment ID",
    "Exact reviewer comment",
    "Scientific issue",
    "Required action",
    "Analysis required",
    "Manuscript section",
    "Figure/table affected",
    "Evidence required",
    "Response location",
    "Status",
    "Remaining risk",
]


def f0(x):
    return f"{x:,.0f}"


def f1(x):
    return f"{x:,.1f}"


def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


def parse(text: str) -> tuple[str, list[dict]]:
    i_ed = text.index("Dear Tatsuki")
    i_r2 = text.index("2. Reviewer 2")
    i_r1 = text.index("3. Reviewer 1")
    i_end = text.index("以上が")
    editor = text[i_ed:i_r2].split("⸻")[0].strip()
    out = []
    for rev, prefix, block in (
        ("Reviewer 2", "R2", text[i_r2:i_r1]),
        ("Reviewer 1", "R1", text[i_r1:i_end]),
    ):
        cur = None
        for line in block.splitlines()[1:]:
            s = line.strip()
            m = HEAD.match(s)
            if m:
                cur = {
                    "reviewer": rev,
                    "id": f"{prefix}-{m.group(2) or 'G'}",
                    "label": s,
                    "text": [],
                }
                out.append(cur)
            elif cur is not None and s and s != "⸻" and s not in SKIP:
                if not s.startswith("Initial submission"):
                    cur["text"].append(s)
    for c in out:
        c["text"] = "\n\n".join(c["text"])
    return editor, out


def values() -> dict:
    cfg = yaml.safe_load(open("config/production.yaml"))
    conv = pd.read_csv(R / "convergence/convergence_summary.csv")
    c1 = conv[(conv.dt_h == 1.0) & (conv.cells == 24)].iloc[0]
    rc = pd.read_csv(R / "pareto/front_recheck_fine.csv")
    o = "s_event_max_kg_per_m"
    drel = np.abs(rc[f"{o}__dt0.0625"] - rc[f"{o}__dt1"]) / np.maximum(
        np.abs(rc[f"{o}__dt0.0625"]), 1.0
    )
    fs = pd.read_csv(R / "pareto/front_summary.csv").set_index("set")
    fine = pd.read_csv(R / "pareto/front_summary_fine_recheck.csv").set_index("set")
    gap = pd.read_csv(R / "pareto/uniform_gap_coverage.csv").set_index("set").loc["combined"]
    diag = pd.read_csv(R / "pareto/run_diagnostics.csv")
    bud = pd.read_csv(R / "review/search_budgets.csv").set_index("search")
    modes = ["geometry", "surface", "joint"]
    frc = pd.read_csv(R / "review/factor_rank_correlation_summary.csv").set_index(
        ["class", "objective", "factor"]
    )
    jd = pd.read_csv(R / "review/release_jump_drivers.csv")
    rl = pd.read_csv(R / "review/roof_length_sensitivity.csv").set_index("roof_length_m")
    ut = pd.read_csv(R / "review/uniform_threshold_check.csv")
    wx = pd.read_csv(R / "weather/synthetic_summary.csv").set_index("scenario")
    jp = pd.read_csv("revision_r1/JAPAN_SNOW_POPULATION_EVIDENCE.csv").set_index("item")
    roof, surf = cfg["roof"], cfg["surface"]
    return {
        "conv_pairs": f"{int(conv.pairs.max()):,}",
        "s_agree_1h": pct(c1["s_event_max_kg_per_m__agree_frac"]),
        "max_abs": f0(c1["s_event_max_kg_per_m__max_abs"]),
        "dt_prod": f"{json.loads((R / 'convergence/production_dt_choice.json').read_text())['production_dt_h']:g}",
        "fine_p95": pct(np.percentile(drel, 95)),
        "hv_u": f"{fs.loc['uniform', 'hv_max_x1.1']:.4f}",
        "hv_j": f"{fs.loc['joint', 'hv_max_x1.1']:.4f}",
        "hv_u_fine": f"{fine.loc['uniform', 'hv_max_x1.1_fine']:.4f}",
        "hv_j_fine": f"{fine.loc['joint', 'hv_max_x1.1_fine']:.4f}",
        "gap_pairs": str(int(gap.pairs_in_uniform_gap)),
        "gap_lo": f1(gap.uniform_gap_lo),
        "gap_hi": f0(gap.uniform_gap_hi),
        "n_runs": str(len(diag)),
        "n_uniform": str(int(bud.loc["uniform_exhaustive", "objective_evaluations"])),
        "n_grid": f"{int(bud.loc['uniform_continuous_grid', 'objective_evaluations']):,}",
        "graded_evals": f"{int(bud.loc[modes, 'objective_evaluations'].sum()):,}",
        "evals": f"{int(bud.objective_evaluations.sum()):,}",
        "runtime_min": f0(bud.loc[modes, "runtime_s_total"].sum() / 60),
        "per_run": f"{cfg['optimizer']['population'] * cfg['optimizer']['generations']:,}",
        "rho_ua": f"{frc.loc[('uniform_shedding', 'l_max_kg_per_m', 'adhesion_factor'), 'median_rho']:.2f}",
        "rho_ia": f"{frc.loc[('graded_intermediate', 's_event_max_kg_per_m', 'adhesion_factor'), 'median_rho']:.2f}",
        "jump_frac": pct(jd.jump_fraction.iloc[0], 0),
        "rl4": str(int(rl.loc[4.0, "graded_pairs_in_gap"])),
        "rl12": str(int(rl.loc[12.0, "graded_pairs_in_gap"])),
        "n_eq": str(int(ut.release_equals_retained.sum())),
        "n_shed": str(len(ut)),
        "deaths_pct": str(jp.iloc[8]["value"]) if "value" in jp else "",
        "cp_swe": f0(wx.loc["cold_persistent", "snowfall_we_kg_m2"]),
        "mw_swe": f0(wx.loc["maritime_warming", "snowfall_we_kg_m2"]),
        "si_swe": f0(wx.loc["severe_inland", "snowfall_we_kg_m2"]),
        "cp_t": f"{wx.loc['cold_persistent', 't_mean_c']:.1f}",
        "mw_t": f"{wx.loc['maritime_warming', 't_mean_c']:.1f}",
        "cp_r": f0(wx.loc["cold_persistent", "rain_mm"]),
        "mw_r": f0(wx.loc["maritime_warming", "rain_mm"]),
        "mu_list": ", ".join(f"{x['mu_static']}" for x in surf["discrete_classes"].values()),
        "smin": str(roof["slope_bounds_deg"][0]),
        "smax": str(roof["slope_bounds_deg"][1]),
        "adj": str(roof["adjacent_slope_limit_deg"]),
        "f_lo": str(surf["static_friction_bounds"][0]),
        "f_hi": str(surf["static_friction_bounds"][1]),
        "a_lo": f0(surf["adhesion_bounds_pa"][0]),
        "a_hi": f0(surf["adhesion_bounds_pa"][1]),
    }


def main() -> None:
    src = sorted((PRIV / "reviewer_comments").glob("CRST-*.txt"))[-1]
    editor, comments = parse(src.read_text())
    resp = yaml.safe_load((OUT / "responses.yaml").read_text())
    ids = [c["id"] for c in comments]
    missing = [i for i in ids if i not in resp]
    extra = [k for k in resp if k != "E" and k not in ids]
    assert not missing and not extra, (missing, extra)
    v = values()
    for r in resp.values():
        for k in list(r):
            r[k] = re.sub(r"\{(\w+)\}", lambda m: v.get(m.group(1), m.group(0)), str(r[k]))
    order = ["Reviewer 1", "Reviewer 2"]
    comments.sort(key=lambda c: (order.index(c["reviewer"]), ids.index(c["id"])))
    plain = re.compile(r"_\{([^}]*)\}|\^\{([^}]*)\}")
    rows = [
        {
            "Reviewer": c["reviewer"],
            "Comment ID": c["id"],
            "Exact reviewer comment": f"{c['label']}: {c['text']}",
            "Scientific issue": resp[c["id"]]["issue"],
            "Required action": resp[c["id"]]["action"],
            "Analysis required": plain.sub(
                lambda m: m.group(1) or m.group(2), resp[c["id"]]["analysis"]
            ),
            "Manuscript section": resp[c["id"]]["section"],
            "Figure/table affected": resp[c["id"]]["figtab"],
            "Evidence required": resp[c["id"]]["evidence"],
            "Response location": f"Response letter, {c['reviewer']}, {c['label']}",
            "Status": resp[c["id"]]["status"],
            "Remaining risk": plain.sub(lambda m: m.group(1) or m.group(2), resp[c["id"]]["risk"]),
        }
        for c in comments
    ]
    mat = pd.DataFrame(rows, columns=COLUMNS)
    mat.to_csv(OUT / "REVIEWER_RESPONSE_MATRIX.csv", index=False)
    with pd.ExcelWriter(OUT / "REVIEWER_RESPONSE_MATRIX.xlsx", engine="xlsxwriter") as xw:
        mat.to_excel(xw, index=False, sheet_name="matrix")
        ws, wb = xw.sheets["matrix"], xw.book
        wrap = wb.add_format({"text_wrap": True, "valign": "top"})
        for k, w in enumerate([11, 8, 70, 30, 30, 30, 20, 18, 30, 30, 18, 30]):
            ws.set_column(k, k, w, wrap)
        ws.freeze_panes(1, 0)

    doc = docx.Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Times New Roman", docx.shared.Pt(11)
    doc.add_heading("Response to the Editor and Reviewers", 0)
    para(doc, "CRST-D-26-01129", bold_lead="Manuscript number: ")
    para(
        doc,
        "Functionally graded roofs for passive snow management: nominal trade-off expansion limited by constructability and timestep sensitivity",
        bold_lead="Submitted title: ",
    )
    para(
        doc,
        "Reviewer comments are reproduced verbatim in italics, followed by our response. Section, equation, figure and table numbers refer to "
        "the revised manuscript; a marked-up version against the submitted file is supplied.",
    )
    doc.add_heading("Editor", 1)
    for blk in editor.split("\n\n"):
        if blk.strip():
            doc.add_paragraph(blk.strip()).runs[0].italic = True
    para(doc, resp["E"]["response"], bold_lead="Response: ")
    for rev in order:
        doc.add_heading(rev, 1)
        for c in (c for c in comments if c["reviewer"] == rev):
            doc.add_heading(c["label"], 2)
            for blk in c["text"].split("\n\n"):
                doc.add_paragraph(blk).runs[0].italic = True
            para(doc, resp[c["id"]]["response"], bold_lead="Response: ")
            para(doc, f"{resp[c['id']]['section']}", bold_lead="Changes in the manuscript: ")
    doc.save(OUT / "response_to_reviewers_R1.docx")
    print(len(comments), "comments;", mat.Status.value_counts().to_dict())


if __name__ == "__main__":
    main()
