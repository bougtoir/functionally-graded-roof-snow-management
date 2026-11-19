"""Build the R1 clean manuscript from canonical results (no hard-coded results)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

sys.path.insert(0, "src")
from graded_roof import omml as M  # noqa: E402
from graded_roof.manuscript import _add_line_numbering, _reference_text  # noqa: E402

R = Path("results/r1")
OUT = Path("manuscript/r1")
O = ["l_max_kg_per_m", "s_event_max_kg_per_m"]  # noqa: E741
TITLE = (
    "Spatially graded roofs for passive snow management in heavy-snowfall regions: "
    "constructable intermediate retention-release trade-offs under a physical event metric"
)


def f0(x):
    return f"{x:,.0f}"


def f1(x):
    return f"{x:,.1f}"


def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


class Refs:
    def __init__(self):
        a = pd.read_csv("references/literature_database.csv")
        b = pd.read_csv(
            "references/references_r1_additional.csv",
            dtype={"volume": str, "issue": str, "pages_or_article_number": str},
        )
        self.db = pd.concat([a, b], ignore_index=True).set_index("record_id")
        self.order: list[str] = []

    def cite(self, *ids):
        nums = []
        for i in ids:
            if i not in self.db.index:
                raise KeyError(i)
            if i not in self.order:
                self.order.append(i)
            nums.append(self.order.index(i) + 1)
        nums = sorted(nums)
        return "[" + ",".join(str(n) for n in nums) + "]"

    def text(self, rid):
        row = self.db.loc[rid].copy()
        row["official_url"] = row.get("official_url", row.get("url", ""))
        if pd.isna(row["official_url"]):
            row["official_url"] = row.get("url", "")
        return _reference_text(row)


def values():
    v = {}
    v["cfg"] = yaml.safe_load(open("config/production.yaml"))
    v["conv"] = pd.read_csv(R / "convergence/convergence_summary.csv")
    v["runs"] = pd.read_csv(R / "convergence/convergence_runs.csv")
    v["dt"] = json.loads((R / "convergence/production_dt_choice.json").read_text())[
        "production_dt_h"
    ]
    v["fs"] = pd.read_csv(R / "pareto/front_summary.csv").set_index("set")
    v["gap"] = pd.read_csv(R / "pareto/uniform_gap_coverage.csv").set_index("set")
    v["diag"] = pd.read_csv(R / "pareto/run_diagnostics.csv")
    v["seedhv"] = pd.read_csv(R / "pareto/per_seed_budget_hypervolume.csv")
    v["fu"] = pd.read_csv(R / "pareto/front_uniform.csv")
    v["fc"] = pd.read_csv(R / "pareto/front_combined.csv")
    v["recheck"] = pd.read_csv(R / "pareto/front_recheck_fine.csv")
    v["fine"] = pd.read_csv(R / "pareto/front_summary_fine_recheck.csv").set_index("set")
    v["rob"] = pd.read_csv(R / "robustness/robustness_summary.csv")
    v["evs"] = pd.read_csv(R / "event_sensitivity/event_sensitivity_summary.csv").set_index(
        "variant"
    )
    v["jma"] = pd.read_csv(R / "jma/jma_runs.csv")
    v["jmaf"] = pd.read_csv(R / "jma/jma_forcing_summary.csv")
    v["ucont"] = pd.read_csv(R / "optimization/uniform_continuous_grid_evaluated.csv")
    v["wx"] = pd.read_csv(R / "weather/synthetic_summary.csv")
    v["jp"] = pd.read_csv("revision_r1/JAPAN_SNOW_POPULATION_EVIDENCE.csv").set_index("item")
    return v


def para(doc, text, style=None, bold_lead=None):
    p = doc.add_paragraph(style=style)
    if bold_lead:
        p.add_run(bold_lead).bold = True
    _runs(p, text)
    return p


def _runs(p, text):
    # _{...} subscript, ^{...} superscript (font-based)
    for tok in re.split(r"(_\{[^}]*\}|\^\{[^}]*\})", text):
        if not tok:
            continue
        if tok.startswith("_{"):
            p.add_run(tok[2:-1]).font.subscript = True
        elif tok.startswith("^{"):
            p.add_run(tok[2:-1]).font.superscript = True
        else:
            p.add_run(tok)


def table(doc, frame, caption):
    cp = doc.add_paragraph(caption, style="Heading 3")
    cp.paragraph_format.space_before = Pt(14)
    t = doc.add_table(rows=1, cols=len(frame.columns))
    t.style = "Table Grid"
    for i, c in enumerate(frame.columns):
        t.rows[0].cells[i].text = ""
        _runs(t.rows[0].cells[i].paragraphs[0], str(c))
        for r in t.rows[0].cells[i].paragraphs[0].runs:
            r.bold = True
            r.font.size = Pt(9)
    for row in frame.itertuples(index=False):
        cells = t.add_row().cells
        for i, x in enumerate(row):
            cells[i].text = ""
            _runs(cells[i].paragraphs[0], str(x))
            for r in cells[i].paragraphs[0].runs:
                r.font.size = Pt(9)


FIGS = [
    "figure_1_model_and_events",
    "figure_2_synthetic_forcing",
    "figure_3_timestep_convergence",
    "figure_4_constructable_pareto_fronts",
    "figure_5_intermediate_profiles",
    "figure_6_search_budget_hypervolume",
    "figure_7_robustness_q95",
    "figure_8_jma_station_winters",
]


def _first_citing(doc, pattern, after_heading="References"):
    rx = re.compile(pattern)
    for par in doc.paragraphs:
        if par.style.name.startswith("Heading") and par.text.strip() == after_heading:
            return None
        if par.style.name.startswith("Heading") or par.text.startswith(("Table ", "Figure ")):
            continue
        if rx.search(par.text):
            return par
    return None


def place_inline(doc, caps):
    """Move each table and insert each figure right after the paragraph that first cites it."""
    body = doc.element.body
    for par in list(doc.paragraphs):
        m = re.match(r"Table (\d+)\.", par.text)
        if m and par.style.name == "Heading 3":
            tbl = par._p.getnext()
            anchor = _first_citing(doc, rf"Table {m.group(1)}\b")
            if anchor is None:
                raise ValueError(f"Table {m.group(1)} not cited")
            anchor._p.addnext(par._p)
            par._p.addnext(tbl)
    for par in list(doc.paragraphs):
        if par.text.strip() == "Tables" and par.style.name == "Heading 1":
            body.remove(par._p)
    inserted = []
    for i, (name, cap) in enumerate(zip(FIGS, caps, strict=True), 1):
        anchor = _first_citing(doc, rf"Fig\. {i}[a-z]?\b")
        if anchor is None:
            raise ValueError(f"Figure {i} not cited")
        img = doc.add_paragraph()
        img.paragraph_format.keep_with_next = True
        img.add_run().add_picture(str(Path("figures/r1/png") / f"{name}.png"), width=Inches(6.0))
        cp = doc.add_paragraph()
        cp.paragraph_format.space_before = Pt(14)
        _runs(cp, cap)
        pos = anchor._p
        while any(pos.getnext() is e for e in inserted):
            pos = pos.getnext()
        pos.addnext(img._p)
        img._p.addnext(cp._p)
        inserted += [img._p, cp._p]


def build(path: Path) -> dict:
    v = values()
    ref = Refs()
    c = ref.cite
    cfg = v["cfg"]
    conv = v["conv"]
    c24 = conv[conv.cells == 24].set_index("dt_h")
    fs, gap, fine = v["fs"], v["gap"], v["fine"]
    lo, hi = gap.uniform_gap_lo.iloc[0], gap.uniform_gap_hi.iloc[0]
    seeds = gap[gap.index.str.contains("_seed")]
    rob = v["rob"].copy()
    rob["graded"] = rob.segments.str.contains(";")
    rc = v["recheck"]
    drel = {
        o: np.abs(rc[f"{o}__dt0.0625"] - rc[f"{o}__dt1"])
        / np.maximum(np.abs(rc[f"{o}__dt0.0625"]), 1.0)
        for o in O
    }
    nrel = {
        o: np.abs(rc[f"{o}__N48"] - rc[f"{o}__dt1"]) / np.maximum(np.abs(rc[f"{o}__N48"]), 1.0)
        for o in O
    }
    jma = v["jma"].copy()
    jma["graded"] = jma.segments.str.contains(";")
    sw = jma.station_winter.nunique()
    leg = v["runs"]
    probe = leg[
        (leg.cells == 24) & (leg.segments == "24x40d0") & (leg.weather == "severe_inland")
    ].sort_values("dt_h", ascending=False)
    jp = v["jp"]
    pop = re.match(r"(\d+) \(([\d.]+) %", jp.loc[4, "value"])
    pop_m, pop_pct = f"{int(pop.group(1)) / 1000:.1f}", pop.group(2)
    uc = v["ucont"]
    wx = v["wx"]
    wxs = wx.set_index("scenario")
    diag = v["diag"]
    evs = v["evs"]
    hv_last = v["seedhv"][v["seedhv"].generation == v["seedhv"].generation.max()]

    doc = Document()
    st = doc.styles
    from docx.shared import RGBColor

    st["Normal"].font.name = "Times New Roman"
    st["Normal"].font.size = Pt(12)
    st["Normal"].font.color.rgb = RGBColor(0, 0, 0)
    for s in ("Title", "Heading 1", "Heading 2", "Heading 3"):
        st[s].font.name = "Times New Roman"
        st[s].font.color.rgb = RGBColor(0, 0, 0)
    _add_line_numbering(doc)
    meta = yaml.safe_load(open("manuscript/author_metadata.yaml"))
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(TITLE)
    a = meta["authors"][0]
    for t in (a["name"] + "*", a["affiliation"]):
        q = doc.add_paragraph(t)
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"*Corresponding author: {a['name']}, {a['postal_address']}, {a['email']}")

    gj = gap.loc["combined"]
    doc.add_heading("Abstract", 1)
    para(
        doc,
        f"In Japan's heavy-snowfall areas, {jp.loc[8, 'value']}% of snow-related deaths occur during snow removal, while roofs that shed snow "
        "create eave-release hazards; roof designs between full retention and full shedding have not been examined under explicit constructability "
        "limits. I asked whether spatial grading of slope and surface class along a constructable roof creates retention-release trade-offs that "
        "uniform roofs cannot provide. A reduced-order ridge-to-eave model with Coulomb-adhesion failure, exact threshold-crossing times and "
        "work-energy runout was forced by three synthetic winters. Release hazard was quantified by a pre-specified physical event metric, the "
        "largest integrated eave-release mass per event (S_{event,max}), replacing a per-timestep metric that halved whenever the timestep halved; "
        "every tested timestep met a pre-specified convergence criterion. Constructability rules were enforced inside NSGA-II by a feasible "
        f"encoding, and graded searches were compared with all {len(pd.read_csv(R / 'optimization/uniform_constructable_evaluated.csv'))} "
        f"constructable uniform roofs. In the model, uniform roofs either shed nearly all snow (maximum retained mass L_{{max}} up to {f1(lo)} "
        f"kg m^{{-1}}) or retained all of it ({f0(hi)} kg m^{{-1}}). Graded roofs added {int(gj.pairs_in_uniform_gap)} nondominated intermediate "
        f"combinations (S_{{event,max}} {f1(gj.S_min)}-{f1(gj.S_max)} kg m^{{-1}}), reproduced in all {len(seeds)} runs and at dt = 0.0625 h, but changed "
        f"normalised hypervolume only from {fs.loc['uniform', 'hv_max_x1.1']:.3f} to {fs.loc['joint', 'hv_max_x1.1']:.3f}. Under parameter and "
        "forcing uncertainty these intermediate options persisted, but their 95th-percentile releases were an order of magnitude larger than "
        "nominal. These model-derived results identify spatial grading as a configurable means of intermediate retention rather than a general "
        "improvement; the model is verified numerically but not validated against roof observations.",
    )
    doc.add_paragraph(
        "Keywords: roof snow; snow shedding; snow retention; heavy-snowfall areas; constructability; multiobjective optimisation; reduced-order model"
    )

    doc.add_heading("1. Introduction", 1)
    para(
        doc,
        f"Heavy snowfall shapes building practice across much of Japan. Under the Act on Special Measures for Heavy Snowfall Areas {c('JPR04')}, "
        f"{jp.loc[1, 'value']} municipalities are designated heavy-snowfall areas, covering {jp.loc[3, 'value']}% of the national land and "
        f"{pop_m} million people, about {pop_pct}% of the national population {c('JPR01')}. Snow-related deaths numbered {jp.loc[7, 'value']} in the "
        f"FY2023 winter; over the preceding decade {jp.loc[8, 'value']}% occurred during snow removal and {jp.loc[9, 'value']}% "
        f"of those victims were aged 65 or older, with falls from roofs and falling roof snow among the dominant accident types {c('JPR02')}. "
        f"Annual snowfall normals reach {jp.loc[11, 'value']} cm in Sapporo and {jp.loc[12, 'value']} cm in Aomori {c('JPR05')}. "
        "Reducing the need to climb roofs and the hazard of uncontrolled releases is therefore both a structural and a public-safety problem.",
    )
    para(
        doc,
        f"The legal framework sets loads, not roof-snow strategies. Article 86 of the Order for Enforcement of the Building Standards Act {c('JPR03')} "
        "defines the snow load from unit snow weight, horizontal projected area and design snow depth; it allows a slope-dependent shape "
        "coefficient for roofs that shed snow, withholds this reduction where snow guards prevent sliding, requires consideration of uneven "
        "snow, and permits a reduced design depth only where roof clearing is customary and its conditions are posted. Retention, shedding, "
        f"melting and load-resisting roofs are thus design choices described in regional technical guidance {c('JP02', 'JP03')} and historical "
        f"practice {c('JP01', 'JP10')}, not in binding rules. Regional guidance for detached houses distinguishes shedding, retention (load-resisting) "
        "and melting approaches and identifies the burdens that the two objectives of this study represent: retained load and clearing work on "
        f"retaining roofs, and falling snow and the clear area it requires below shedding roofs {c('JP02', 'JP03', 'JP09')}. The model in this paper "
        "does not compute code snow loads and makes no compliance claim.",
    )
    para(
        doc,
        f"Roof-snow research has concentrated on drift and deposition {c('CRST01', 'CRST02', 'CRST03', 'CRST04', 'CRST05', 'CRST06', 'CRST08', 'CRST09', 'JP08')} "
        f"and on load monitoring {c('CRST11')}. Sliding depends on surface roughness, water content, ageing and adhesion {c('JP05', 'JP06', 'CRST12')}, "
        f"snow guards change retention {c('JP04')}, and melting systems trade energy for clearance {c('JP07', 'CRST10')}; sliding models for inclined "
        f"photovoltaic panels show the sensitivity of release to interface parameters {c('CRST07')}. Municipal guidance highlights the hazard of "
        f"falling roof snow and ice {c('JP09')}.",
    )
    para(
        doc,
        "Roof-snow stability, that is, whether and when snow on a roof surface fails and slides, precedes and differs from the mechanisms "
        "addressed by structural-failure and impact-hazard studies. Analyses of roof rock-beam failure at mine roadway intersections concern the "
        f"collapse of the load-bearing structure itself {c('WANG26')}, and coupled rockfall-bridge assessments concern the trajectory and impact "
        f"damage of a mass already in motion {c('ZHANG26')}. The present study addresses only the onset and size of releases from the roof surface; "
        "the structural capacity of the roof and impact damage below the eave would require structural and trajectory models of the kind used in "
        "those studies and are not evaluated.",
    )
    para(
        doc,
        "I use the term functionally graded roof, borrowed from materials whose properties vary with position, for a roof whose slope or surface "
        "properties vary deliberately from ridge to eave. Practical realisations are piecewise: multi-pitch or curved profiles assembled from "
        "segments of constant pitch, and zones of different roofing finish, for example smooth coated steel that promotes sliding and rough or aged "
        f"finishes or snow-stop elements that promote retention {c('JP04', 'JP05', 'JP06')}. Such roofs are passive: unlike roof heating and "
        f"snow-melting systems, which clear snow at a continuing energy and operating cost {c('JP07', 'CRST10')}, they need no energy in operation. "
        "Whether varying slope and surface along a single roof can place it between the retention and shedding extremes has not, to my knowledge, "
        "been examined under explicit constructability limits.",
    )
    para(
        doc,
        "Physics-resolving methods address other parts of the problem. Computational fluid dynamics and wind-tunnel studies predict where wind "
        f"deposits snow {c('CRST04', 'CRST09')}, and energy-balance melt models predict melt and refreezing; neither is designed to decide, tens of "
        "thousands of times within an optimisation, whether a snow layer on a sloping surface fails by sliding. To first order, release onset on a "
        "sloping roof is governed by the balance between the downslope weight of the snow and interface resistance from friction and adhesion "
        f"{c('JP05', 'JP06', 'CRST12')}, which a threshold model represents at a cost that permits a constrained design search. The price is that "
        "results are comparative and model-derived, and omitted processes limit their transfer to real roofs (Section 4.2).",
    )
    para(
        doc,
        "The question tested here was whether spatial grading of slope and surface, restricted to roofs that can be built from a small number of "
        "segments and standard finishes, produces physically interpretable, numerically stable and robust retention-release trade-offs that uniform "
        "roofs cannot provide (workflow in Fig. 1c). Constructability is part of the question because a graded profile that cannot be built is not "
        "a design option. In the model, retention or shedding of each part of the roof is decided by the local balance between the downslope weight "
        "of the snow and interface resistance; grading changes this balance along the roof so that snow released upslope can stop on a retaining "
        "segment. Wind redistribution, phase changes and snow heterogeneity also control real releases, but they were held fixed or omitted so that "
        "the effect of the designed variables could be isolated. A negative or limited answer was admissible. Compared with the originally "
        "submitted analysis, the release metric, the transport scheme, the treatment of constructability and the number of optimisation seeds were "
        "revised; all changes are listed in Section 2.8 and the original outputs are retained.",
    )

    doc.add_heading("2. Methods", 1)
    doc.add_heading("2.1 Reduced-order roof-snow model", 2)
    rf = cfg["roof"]
    phys = cfg["snow"]
    para(
        doc,
        f"A {rf['length_m']:.0f} m ridge-to-eave strip of unit width was divided into {rf['cells']} cells, each with slope, static and kinetic "
        "friction and adhesion. The cells are fixed parts of the roof; only the snow they carry moves. Each cell i holds snow mass m_{i} per unit "
        "plan area, a snow volume and an age moment, the mass-weighted sum of time since deposition, from which the mean snow age a_{i} follows. "
        "Between releases, mass changes by snowfall P and melt M_{i}:",
    )
    M.add_equation(
        doc.add_paragraph(),
        M.frac(["d", M.sub("m", "i")], "d t"),
        " = P − ",
        M.sub("M", "i"),
        ",    ",
        M.sub("M", "i"),
        " = ",
        M.sub("f", "m"),
        " ",
        M.func("max", "(T, 0)"),
        " + ",
        M.sub("f", "r"),
        " R",
        number="1",
    )
    para(
        doc,
        f"where T is air temperature, R the rain rate, f_{{m}} = {phys['melt_factor_kg_m2_c_h']} kg m^{{-2}} °C^{{-1}} h^{{-1}} a degree-hour melt "
        f"factor and f_{{r}} = {phys['rain_heat_factor_kg_m2_mm']} kg m^{{-2}} mm^{{-1}} a rain-heat factor. Melt removes mass, volume and age moment "
        f"in proportion. Fresh snow enters at {phys['initial_density_kg_m3']:.0f} kg m^{{-3}} and compacts towards ρ_{{max}} = "
        f"{phys['maximum_density_kg_m3']:.0f} kg m^{{-3}},",
    )
    M.add_equation(
        doc.add_paragraph(),
        M.frac("dρ", "d t"),
        " = ",
        M.sub("k", "c"),
        " (",
        M.sub("ρ", "max"),
        " − ρ)",
        number="2",
    )
    para(
        doc,
        f"with k_{{c}} = {phys['compaction_rate_per_day']} d^{{-1}}; compaction changes snow depth but not mass, and density does not enter the "
        "failure criterion below. Static and kinetic friction coefficients increase with snow age and decrease near melting:",
    )
    M.add_equation(
        doc.add_paragraph(),
        "μ = ",
        M.sub("μ", "0"),
        " [1 + α (1 − ",
        M.func("exp", ["(−", M.frac("a", M.sub("τ", "a")), ")"]),
        ")] [1 − β ",
        M.func("exp", ["(−", M.sup(["(", M.frac(["T − ", M.sub("T", "c")], "w"), ")"], "2"), ")"]),
        "]",
        number="3",
    )
    para(
        doc,
        f"where μ_{{0}} is the surface-class value, α = {phys['friction_age_gain']}, τ_{{a}} = {phys['dynamic_friction_age_scale_days']:g} d, "
        f"β = {phys['near_melt_friction_loss']}, T_{{c}} = {phys['near_melt_center_c']} °C and w = {phys['near_melt_width_c']} °C. A cell with "
        "mass m per unit area failed when the downslope weight exceeded the Coulomb-adhesion resistance:",
    )
    M.add_equation(
        doc.add_paragraph(),
        "m g ",
        M.func("sin", "θ"),
        " ≥ ",
        M.sub("μ", "s"),
        " m g ",
        M.func("cos", "θ"),
        " + c",
        number="4",
    )
    para(
        doc,
        "where θ is slope, μ_{s} static friction and c adhesion. Because snowfall within a step is integrated exactly, the failure time is found "
        "as the exact crossing of the threshold mass m* = c/[g(sin θ − μ_{s} cos θ)] within the step rather than at step end. A released slab "
        "travels downslope with kinetic friction μ_{k}; its speed follows the work-energy balance",
    )
    M.add_equation(
        doc.add_paragraph(),
        M.sup(M.sub("v", "j+1"), "2"),
        " = ",
        M.sup(M.sub("v", "j"), "2"),
        " + 2 g Δx (",
        M.func("sin", M.sub("θ", "j")),
        " − ",
        M.sub("μ", "k,j"),
        " ",
        M.func("cos", M.sub("θ", "j")),
        ")",
        number="5",
    )
    para(
        doc,
        "and it stops where the speed reaches zero or leaves at the eave. Mass resting in cells it crosses that are themselves at or above threshold is "
        "entrained inelastically. Cells that cannot hold any snow (sin θ > μ_{s} cos θ and c = 0) route incoming snowfall continuously to the eave or "
        "to the first retaining cell. Mass balance (input = eave release + melt + residual) was checked in every run.",
    )
    para(
        doc,
        "The friction and adhesion values of the three surface classes and the ageing and near-melt coefficients were not calibrated against "
        "roof measurements. They were set to span low, intermediate and high interface resistance, consistent in ordering with roofing-surface "
        f"and adhesion studies {c('JP05', 'JP06', 'CRST12')} (values and provenance in Supplementary Table S1), and their influence was quantified "
        "by the uncertainty analysis (Section 2.7). The model represents only retention and release because these are what the designed "
        "variables control directly. Uneven snow distribution by wind, liquid-water retention in the snowpack and the structural response of the "
        "roof are not modelled; their consequences are discussed in Section 4.2.",
    )
    doc.add_heading("2.2 Outcomes", 2)
    para(
        doc,
        "L_{max} is the maximum retained roof mass per metre width over the winter. The primary release outcome is the largest physical event mass",
    )
    M.add_equation(
        doc.add_paragraph(),
        M.sub("S", "event,max"),
        " = ",
        M.sub("max", "e"),
        " ",
        M.sub("M", "e"),
        ",   ",
        M.sub("M", "e"),
        " = ",
        M.nary("∑", "i∈e", "", M.sub("m", "i")),
        " + ",
        M.nary("∫", M.sub("t", "e,0"), M.sub("t", "e,1"), "q(t) dt"),
        number="6",
    )
    para(
        doc,
        "where m_{i} are slab masses leaving the eave at their exact times and q(t) is continuous eave outflow. An event starts when a slab leaves "
        f"or q exceeds {cfg.get('event_q_min', 1.0)} kg m^{{-1}} h^{{-1}}, and ends when no such activity occurs for 1 h. The definition, tie rules and secondary "
        "fixed-window metrics (largest release in any 10 min, 1 h and 3 h window) were specified before any revised result was generated (Fig. 1b). The submitted "
        "per-timestep maximum is reported only as a diagnostic. Both objectives were taken as the worst case over the three winters.",
    )
    doc.add_heading("2.3 Weather forcing", 2)
    para(
        doc,
        "Three deterministic 336-h synthetic winters (cold persistent, maritime warming, severe inland) were defined in continuous time: Gaussian "
        "snowfall pulses, linear warming with a diurnal cycle, and terminal rain-on-snow. Step totals are exact integrals, so every timestep sees "
        f"the same storm (water-equivalent snowfall {f0(wx.snowfall_we_kg_m2.min())}-{f0(wx.snowfall_we_kg_m2.max())} kg m^{{-2}}; Fig. 2). "
        f"Observed JMA daily records for {jma.station_winter.str.split('_').str[0].nunique()} stations and {sw} station-winters {c('JPR06')} were used only "
        "as supplementary scenarios, spreading daily totals uniformly over 24 h. These ground observations are not roof-snow validation data, "
        "and the synthetic winters are stylised and were not fitted to any station record. "
        f"The cold persistent and maritime warming winters have similar snowfall ({f0(wxs.loc['cold_persistent', 'snowfall_we_kg_m2'])} and "
        f"{f0(wxs.loc['maritime_warming', 'snowfall_we_kg_m2'])} kg m^{{-2}}) but differ in mean temperature "
        f"({wxs.loc['cold_persistent', 't_mean_c']:.1f} and {wxs.loc['maritime_warming', 't_mean_c']:.1f} °C) and rain "
        f"({wxs.loc['cold_persistent', 'rain_mm']:.0f} and {wxs.loc['maritime_warming', 'rain_mm']:.0f} mm); the severe inland winter has "
        f"{f0(wxs.loc['severe_inland', 'snowfall_we_kg_m2'])} kg m^{{-2}} with air temperature never above {wxs.loc['severe_inland', 't_max_c']:.1f} °C "
        "(Fig. 2a-c). Daily mean temperature and precipitation of the JMA station-winters are shown in Fig. 2d-f.",
    )
    doc.add_heading("2.4 Numerical verification", 2)
    para(
        doc,
        "Before optimisation, all constructable uniform roofs and 60 random constructable graded roofs were simulated at dt = 1, 0.5, 0.25, 0.125 "
        "and 0.0625 h (reference) with 24 cells, and at 48 and 96 cells "
        f"({int(conv.pairs.max())} unique design-winter pairs). A timestep was acceptable if at least 95% of pairs agreed with the "
        "reference within max(2%, 1 kg m^{-1}) for L_{max}, S_{event,max}, S_{1h,max} and total release, at least 90% had event counts within one, "
        "and mass-balance error was below 10^{-6} kg m^{-1}; the coarsest acceptable step was used. The criterion is an aggregate one: a passing timestep "
        "may still contain individual pairs outside tolerance, which are reported. All final nondominated designs were then "
        "re-evaluated at 0.0625 h and at 48 cells.",
    )
    doc.add_heading("2.5 Constructable optimisation", 2)
    bud = pd.read_csv(R / "review/search_budgets.csv").set_index("search")
    MODES_ = ["geometry", "surface", "joint"]
    para(
        doc,
        "Candidates were decoded from a unit hypercube into piecewise-constant segments that satisfy every rule by construction: segments of at "
        f"least {rf['minimum_segment_cells']} cells, at most {rf['maximum_transitions']} transitions, integer slopes {rf['slope_bounds_deg'][0]}-{rf['slope_bounds_deg'][1]} degrees, "
        f"adjacent slope changes of at most {rf['adjacent_slope_limit_deg']} degrees, and one of three surface classes (smooth metal, aged coated metal, "
        "rough retention surface). Geometry-only (single class), surface-only (single slope) and joint searches each used NSGA-II with population "
        f"{cfg['optimizer']['population']}, {cfg['optimizer']['generations']} generations and {diag.seed.nunique()} seeds. The uniform reference was the exhaustive "
        f"set of constructable uniform roofs; a continuous uniform grid of {len(uc):,} designs (slope {rf['slope_bounds_deg'][0]}-{rf['slope_bounds_deg'][1]} "
        f"degrees, static friction {cfg['surface']['static_friction_bounds'][0]}-{cfg['surface']['static_friction_bounds'][1]}, adhesion "
        f"{cfg['surface']['adhesion_bounds_pa'][0]:.0f}-{cfg['surface']['adhesion_bounds_pa'][1]:.0f} Pa) was evaluated as a sensitivity. The class values "
        "(μ_{s}, μ_{k}, c) were "
        + "; ".join(
            f"{k.replace('_', ' ')} ({x['mu_static']}, {x['mu_kinetic']}, {x['adhesion_pa']:.0f} Pa)"
            for k, x in cfg["surface"]["discrete_classes"].items()
        )
        + f". Each run evaluated {cfg['optimizer']['population'] * cfg['optimizer']['generations']:,} candidates; the {len(diag)} graded runs together "
        f"evaluated {int(bud.loc[MODES_, 'objective_evaluations'].sum()):,} objective vectors ({int(bud.loc[MODES_, 'unique_designs_simulated'].sum()):,} "
        f"distinct designs) in {bud.loc[MODES_, 'runtime_s_total'].sum() / 60:.0f} min on two cores ({bud.loc[MODES_, 'runtime_s_per_seed_median'].min():.0f}-"
        f"{bud.loc[MODES_, 'runtime_s_per_seed_median'].max():.0f} s per run), against {int(bud.loc['uniform_exhaustive', 'objective_evaluations'])} exhaustive "
        "uniform evaluations. The comparison is therefore asymmetric: the uniform set is complete, whereas graded fronts are heuristic approximations.",
    )
    doc.add_heading("2.6 Frontier comparison", 2)
    para(
        doc,
        "Fronts were compared by normalised hypervolume (reference point 1.1 times the largest observed objectives, with 1.05 and 1.5 as "
        "sensitivities), additive epsilon in both directions, matched-objective improvement, unique objective pairs, per-seed variability and "
        "hypervolume after 15, 30 and 45 generations. The number of graded pairs lying inside the L_{max} gap of the uniform front is reported "
        "as a descriptive summary defined after the fronts were inspected. A segment is a run of adjacent cells with equal slope and surface "
        "class, and a transition is a change between segments. Normalised hypervolume is the fraction of the box between the origin and the "
        "reference point that a front dominates after each objective is divided by its reference value (larger is better). Additive epsilon is "
        "the smallest amount that must be subtracted from every objective of one front for it to weakly dominate the other; normalised epsilon "
        "divides this amount by the reference values. Matched-objective improvement is the relative improvement in one objective at a matched "
        "value of the other, with respect to the uniform front.",
    )
    doc.add_heading("2.7 Robustness and event-definition sensitivity", 2)
    rb = cfg["robustness"]
    cv = rb["coefficient_of_variation"]
    para(
        doc,
        f"Every nondominated design was simulated under {rb['samples']} common random draws (seed {rb['seed']}) of lognormal multipliers on friction "
        f"(CV {cv['friction']}), adhesion ({cv['adhesion']}), fresh-snow density ({cv['fresh_snow_density']}) and snowfall ({cv['snowfall']}), and a normal "
        f"temperature offset (SD {cv['temperature_sd_c']} degrees C); the {int(100 * rb['robust_quantile'])}th percentiles (Q95), computed separately for each objective and therefore not a joint design point, are reported. The event definition was "
        "varied (separation 10 min and 3 h; activity threshold 0.1 and 10 kg m^{-1} h^{-1}) and entrainment was switched off. To identify what "
        "drives robustness losses, Spearman rank correlations between each uncertainty factor and each outcome were computed for every design, "
        "and draws in which an intermediate design released more than ten times its nominal S_{event,max} were compared with the remaining "
        "draws. Finally, the constructable uniform set and all nondominated designs were re-evaluated, without re-optimisation, on roofs 4 m "
        "and 12 m long with 24 cells.",
    )
    doc.add_heading("2.8 Changes from the submitted analysis and reproducibility", 2)
    para(
        doc,
        "The submitted analysis moved snow one cell per step and defined events per timestep, so its release endpoint depended on dt; it also "
        "applied constructability only after optimisation. The revision replaced transport, the release metric and the constraint handling, "
        "increased seeds from three to five, and selected dt by the rule above. The decision-scoring layer of the submitted version (labour-scarcity, "
        "complexity-penalty and transition-penalty selections and the scalar robustness score) was removed, because hard constraints and whole-front "
        "comparisons replace it. Code, configuration, raw public-data snapshots with checksums, "
        "and every table and figure source are in the project repository; the submitted state is preserved under a fixed tag.",
    )

    doc.add_heading("3. Results", 1)
    doc.add_heading("3.1 Numerical convergence", 2)
    para(
        doc,
        "For a smooth 40-degree uniform roof in the severe inland winter, the submitted per-step metric was "
        + ", ".join(f1(x) for x in probe.legacy_s_step_max_kg_per_m.head(3))
        + " kg m^{-1} at dt = "
        + ", ".join(f"{x:g}" for x in probe.dt_h.head(3))
        + " h, whereas S_{event,max} was "
        + ", ".join(f1(x) for x in probe.s_event_max_kg_per_m.head(3))
        + " kg m^{-1} (Fig. 3a). "
        f"At dt = 1 h, {pct(c24.loc[1.0, 's_event_max_kg_per_m__agree_frac'])} of pairs met the S_{{event,max}} tolerance and "
        f"{pct(c24.loc[1.0, 'l_max_kg_per_m__agree_frac'])} met the L_{{max}} tolerance; all steps passed (Fig. 3b, Table 1), so dt = {v['dt']:g} h was used. "
        f"The largest deviations (up to {f0(c24.loc[1.0, 's_event_max_kg_per_m__max_abs'])} kg m^{{-1}}) occurred for designs near a failure threshold. "
        f"Spatial refinement to 48 and 96 cells changed S_{{event,max}} by a 95th-percentile relative amount of "
        f"{pct(conv[(conv.cells == 96)].s_event_max_kg_per_m__p95_rel.iloc[0], 2)}. Mass-balance error was below 10^{{-6}} kg m^{{-1}} in every run.",
    )
    exs = json.loads((R / "review/exception_summary.json").read_text())
    para(
        doc,
        f"At dt = 1 h, {exs['pairs_failing_any_metric']} of {exs['pairs_compared']} pairs failed at least one metric; "
        f"{exs['failing_designs_on_uniform_front']} of the failing designs lie on the uniform front, {exs['failing_designs_on_combined_front']} on the combined front "
        f"and {exs['failing_designs_graded_in_gap']} among the graded designs inside the uniform gap. Rebuilding the fronts entirely from dt = 0.0625 h objectives "
        f"gave the same {exs['gap_fine_dt0.0625']['graded_pairs_in_gap']} graded pairs inside a uniform gap of {f1(exs['gap_fine_dt0.0625']['uniform_gap_lo'])}-"
        f"{f0(exs['gap_fine_dt0.0625']['uniform_gap_hi'])} kg m^{{-1}}. The largest deviation was a rough 28-degree uniform roof that is held by static friction and "
        "fails only while the near-melt friction reduction is active, so its release depends on how finely that short window is resolved.",
    )
    doc.add_heading("3.2 Uniform reference", 2)
    fu = v["fu"]
    para(
        doc,
        f"The constructable uniform front had {int(fs.loc['uniform', 'unique_objective_pairs'])} unique objective pairs (Fig. 4). Smooth roofs of "
        f"{fu[O[0]].idxmin() and int(fu.sort_values(O[0]).segments.iloc[0].split('x')[1].split('d')[0])}-{int(fu[fu[O[0]] < hi].sort_values(O[0]).segments.iloc[-1].split('x')[1].split('d')[0])} degrees "
        f"traded L_{{max}} from {f1(fu[O[0]].min())} to {f1(lo)} kg m^{{-1}} against S_{{event,max}} from {f0(fu[O[1]].max())} to {f1(fu[fu[O[0]] == lo][O[1]].iloc[0])} kg m^{{-1}}; "
        "steep smooth roofs shed frequently, and closely spaced small releases merge into long events. The next uniform option was full retention "
        f"(L_{{max}} {f0(hi)} kg m^{{-1}}, no release). No constructable uniform roof lay between these regimes. The continuous uniform grid, which allows "
        f"non-catalogue friction and adhesion, also had no design between {f1(uc[uc[O[0]] > 0][uc[uc[O[0]] > 0][O[1]] < uc[uc[O[0]] > 0][O[0]] + 1e-6][O[0]].min())} and {f0(uc[O[0]].max())} kg m^{{-1}} on its front.",
    )
    ut = pd.read_csv(R / "review/uniform_threshold_check.csv")
    para(
        doc,
        f"For {int(ut.release_equals_retained.sum())} of the {len(ut)} shedding uniform roofs, the largest event equalled the retained maximum "
        "(L_{max} = S_{event,max}): the whole roof reached its failure threshold and released at once, so the objective pair is set by the "
        "threshold load c/[g(sin θ − μ_{s} cos θ)] rather than by the design search. The remaining shedding roofs released in parts or as "
        "continuous streams. The single uniform objective pair that dominated the submitted analysis was of the first kind.",
    )
    doc.add_heading("3.3 Graded fronts", 2)
    para(
        doc,
        f"All {len(diag)} runs produced only constructable designs, simulating {f0(diag.unique_designs_simulated.min())}-{f0(diag.unique_designs_simulated.max())} unique designs each. "
        f"The geometry, surface and joint fronts had {int(fs.loc['geometry', 'unique_objective_pairs'])}, {int(fs.loc['surface', 'unique_objective_pairs'])} and "
        f"{int(fs.loc['joint', 'unique_objective_pairs'])} unique pairs. Hypervolume was {fs.loc['uniform', 'hv_max_x1.1']:.4f} for the uniform set and "
        f"{fs.loc['geometry', 'hv_max_x1.1']:.4f}, {fs.loc['surface', 'hv_max_x1.1']:.4f} and {fs.loc['joint', 'hv_max_x1.1']:.4f} for the graded sets, with the same ordering under "
        f"both alternative reference points (Table 2). No graded front was dominated anywhere by the uniform front (epsilon 0), and the uniform front needed a "
        f"normalised shift of {fs.loc['joint', 'eps_norm_uniform_to_set']:.4f} to cover the joint front. Matched-objective improvements were small: median "
        f"{pct(fs.loc['joint', 'matched_s_improvement_median'])} in S_{{event,max}} at equal L_{{max}} (maximum {pct(fs.loc['joint', 'matched_s_improvement_maximum'])}).",
    )
    para(
        doc,
        f"The substantive difference lay in the uniform gap. The combined graded fronts contained {int(gj.pairs_in_uniform_gap)} pairs with L_{{max}} between "
        f"{f1(lo)} and {f0(hi)} kg m^{{-1}} and S_{{event,max}} of {f1(gj.S_min)}-{f1(gj.S_max)} kg m^{{-1}}; every one of the {len(seeds)} runs found such pairs "
        f"({int(seeds.pairs_in_uniform_gap.min())}-{int(seeds.pairs_in_uniform_gap.max())} per run). These designs combine steep or smooth shedding segments with a low-slope "
        "or rough retaining segment, so that snow released upslope stops on the roof while a short eave-side zone sheds small amounts (Fig. 5). "
        f"Final-generation hypervolume varied across seeds by at most {hv_last.groupby('mode')['hv_max_x1.1'].agg(lambda x: x.max() - x.min()).max():.4f}, and the change from 30 to 45 "
        f"generations was at most {(v['seedhv'].pivot_table(index=['mode', 'seed'], columns='generation', values='hv_max_x1.1').pipe(lambda d: (d[45] - d[30]).max())):.4f} (Fig. 6).",
    )
    doc.add_heading("3.4 Fine-resolution re-check", 2)
    para(
        doc,
        f"Re-evaluating all {len(rc)} nondominated designs at dt = 0.0625 h changed S_{{event,max}} by a median {pct(np.median(drel[O[1]]), 2)} "
        f"(95th percentile {pct(np.percentile(drel[O[1]], 95), 1)}) and L_{{max}} by a median {pct(np.median(drel[O[0]]), 2)}; refinement to 48 cells changed "
        f"S_{{event,max}} by a median {pct(np.median(nrel[O[1]]), 2)}. With fine-resolution objectives, hypervolume was {fine.loc['uniform', 'hv_max_x1.1_fine']:.4f} "
        f"(uniform) and {fine.loc['joint', 'hv_max_x1.1_fine']:.4f} (joint).",
    )
    doc.add_heading("3.5 Event-definition sensitivity", 2)
    b, s10, s3, ne = (evs.loc[k] for k in ("base", "tau_sep_10min", "tau_sep_3h", "no_entrainment"))
    para(
        doc,
        "The activity threshold (0.1 or 10 kg m^{-1} h^{-1}) did not change any front. The separation time did (Table 3). With 10 min separation, "
        f"closely spaced releases from steep smooth roofs counted as separate events, the uniform front shrank to {int(s10.uniform_front_pairs)} pairs and the "
        f"uniform gap began at {f1(s10.uniform_gap_lo)} kg m^{{-1}}; with 3 h separation it began at {f1(s3.uniform_gap_lo)} kg m^{{-1}}. Graded pairs inside the uniform gap "
        f"numbered {int(b.pairs_in_uniform_gap)} (base), {int(s10.pairs_in_uniform_gap)} (10 min) and {int(s3.pairs_in_uniform_gap)} (3 h), and {int(ne.pairs_in_uniform_gap)} without entrainment. "
        "The existence of intermediate graded options was therefore insensitive to these choices, whereas the release magnitude attributed to shedding roofs "
        "depended strongly on how closely spaced releases are grouped.",
    )
    doc.add_heading("3.6 Robustness", 2)
    rcs = pd.read_csv(R / "robustness/robustness_class_summary.csv").set_index("class")
    rcl = pd.read_csv(R / "robustness/robustness_classified.csv")
    gi, us = rcs.loc["graded_intermediate"], rcs.loc["uniform_shedding"]
    qf = rcl[rcl.on_q95_front & (rcl["class"] == "graded_intermediate")]
    ur = rcl[rcl["class"] == "uniform_retention"]
    para(
        doc,
        f"Uncertainty degraded the intermediate designs strongly (Fig. 7). For the {int(gi.designs)} graded designs inside the nominal uniform gap, "
        f"Q95 S_{{event,max}} ranged from {f0(gi.q95_s_min)} to {f0(gi.q95_s_max)} kg m^{{-1}} (median {f0(gi.q95_s_median)}), against nominal values of at most "
        f"{f1(gi.nominal_s_max)} kg m^{{-1}}; in a median {pct(gi.frac_above_lo_median, 0)} of draws their release exceeded {f1(lo)} kg m^{{-1}}. Uniform shedding roofs "
        f"were similarly sensitive at the retentive end (Q95 S_{{event,max}} {f0(us.q95_s_min)}-{f0(us.q95_s_max)} kg m^{{-1}}). In Q95 space the gap persisted: uniform roofs "
        f"gave Q95 L_{{max}} of at most {f0(us.q95_l_max)} kg m^{{-1}} or full retention ({f0(ur.l_q.iloc[0])} kg m^{{-1}}), whereas {len(qf)} graded designs formed the Q95 front between "
        f"{f0(qf.l_q.min())} and {f0(qf.l_q.max())} kg m^{{-1}} with Q95 S_{{event,max}} of {f0(qf.s_q.min())}-{f0(qf.s_q.max())} kg m^{{-1}}, below every uniform shedding roof. "
        f"Mass-balance error remained below {rcs.max_mass_balance_error.max():.0e} kg m^{{-1}}.",
    )
    frc = pd.read_csv(R / "review/factor_rank_correlation_summary.csv").set_index(
        ["class", "objective", "factor"]
    )
    jd = pd.read_csv(R / "review/release_jump_drivers.csv").set_index("factor")

    def rho(k, o, f):
        return frc.loc[(k, f"{o}_kg_per_m", f"{f}_factor"), "median_rho"]

    dens = frc.xs("density_factor", level="factor").median_rho.abs().max()
    para(
        doc,
        f"Releases larger than ten times nominal occurred in {pct(jd.jump_fraction.iloc[0], 0)} of draws for the intermediate designs. In those "
        f"draws the median friction multiplier was {jd.loc['friction_factor', 'jump_median']:.2f} (other draws "
        f"{jd.loc['friction_factor', 'no_jump_median']:.2f}), the adhesion multiplier {jd.loc['adhesion_factor', 'jump_median']:.2f} "
        f"({jd.loc['adhesion_factor', 'no_jump_median']:.2f}), the snowfall multiplier {jd.loc['snowfall_factor', 'jump_median']:.2f} "
        f"({jd.loc['snowfall_factor', 'no_jump_median']:.2f}) and the temperature offset {jd.loc['temperature_offset_c', 'jump_median']:+.2f} °C "
        f"({jd.loc['temperature_offset_c', 'no_jump_median']:+.2f} °C): weaker interfaces and heavier snowfall let the retaining segment fail and "
        "release its accumulated load in one event. Across intermediate designs, S_{event,max} correlated most with snowfall (median Spearman "
        f"ρ = {rho('graded_intermediate', 's_event_max', 'snowfall'):.2f}) and adhesion ({rho('graded_intermediate', 's_event_max', 'adhesion'):.2f}), "
        f"and less with friction ({rho('graded_intermediate', 's_event_max', 'friction'):.2f}). For uniform shedding roofs, L_{{max}} was controlled "
        f"almost entirely by adhesion (ρ = {rho('uniform_shedding', 'l_max', 'adhesion'):.2f}), as expected from the threshold load. Fresh-snow "
        f"density had no material influence (|ρ| ≤ {dens:.2f}) because it changes snow depth but not the failure criterion.",
    )
    doc.add_heading("3.7 JMA station-winter scenarios", 2)
    js = pd.read_csv(R / "jma/jma_station_summary.csv")
    para(
        doc,
        f"Under the {sw} observed station-winters (snowfall water equivalent {f0(v['jmaf'].snowfall_we_kg_m2.min())}-{f0(v['jmaf'].snowfall_we_kg_m2.max())} kg m^{{-2}}, "
        f"rain {f0(v['jmaf'].rain_mm.min())}-{f0(v['jmaf'].rain_mm.max())} mm), the same designs were re-simulated without re-optimisation (Fig. 8). Because daily snowfall was spread "
        f"uniformly, steep smooth roofs shed as near-continuous streams and the uniform front reduced to {int(js.uniform_front_pairs.max())} pairs in every station-winter: "
        f"a shedding roof with L_{{max}} of {f1(js.uniform_gap_lo.min())}-{f1(js.uniform_gap_lo.max())} kg m^{{-1}}, or full retention. In every station-winter, {int(js.graded_pairs_in_gap.min())}-"
        f"{int(js.graded_pairs_in_gap.max())} graded pairs lay between these options, with S_{{event,max}} of {f1(js.gap_s_event_min.min())}-{f1(js.gap_s_event_max.max())} kg m^{{-1}}. "
        "These scenario results extend the comparison to longer, observed forcing but do not validate roof behaviour.",
    )

    doc.add_heading("3.8 Roof length", 2)
    rl = pd.read_csv(R / "review/roof_length_sensitivity.csv").set_index("roof_length_m")
    para(
        doc,
        "Re-evaluating the same designs on shorter and longer roofs scaled the masses approximately with roof length but did not remove the "
        f"uniform gap or the graded pairs inside it: the gap spanned {f1(rl.loc[4.0, 'uniform_gap_lo'])}-{f0(rl.loc[4.0, 'uniform_gap_hi'])} kg m^{{-1}} "
        f"at 4 m and {f1(rl.loc[12.0, 'uniform_gap_lo'])}-{f0(rl.loc[12.0, 'uniform_gap_hi'])} kg m^{{-1}} at 12 m and contained "
        f"{int(rl.loc[4.0, 'graded_pairs_in_gap'])} and {int(rl.loc[12.0, 'graded_pairs_in_gap'])} graded pairs (8 m: "
        f"{int(rl.loc[8.0, 'graded_pairs_in_gap'])}), with S_{{event,max}} of {f1(rl.loc[4.0, 'gap_s_event_min'])}-{f1(rl.loc[4.0, 'gap_s_event_max'])} "
        f"and {f1(rl.loc[12.0, 'gap_s_event_min'])}-{f1(rl.loc[12.0, 'gap_s_event_max'])} kg m^{{-1}}. Designs were not re-optimised for these lengths.",
    )

    doc.add_heading("4. Discussion", 1)
    para(
        doc,
        "Within this model, spatial grading did not produce a generally better roof: hypervolume, epsilon and matched-objective gains over the "
        "exhaustive constructable uniform set were small. What grading did provide, reproducibly across seeds, was access to intermediate states between "
        "near-complete shedding and full retention, where a roof holds most of its snow and releases less than any shedding uniform roof. "
        "The nominal smallness of those releases was not robust: it depends on a retaining segment holding close to its failure threshold, and modest changes "
        "in friction, adhesion or snowfall convert it into releases of several hundred kg m^{-1}. Uniform roofs reach these "
        "states only through non-catalogue surface properties, if at all. In practice this corresponds to a retention zone combined with a short "
        "controlled-shedding eave zone, a configuration related to snow guards and retention roofs in regional guidance "
        f"{c('JP02', 'JP03', 'JP04')}; the mechanism is physically interpretable (upslope releases stop on a retaining segment).",
    )
    para(
        doc,
        "Whether the intermediate pairs are physical or artefacts can be judged from three results. They persisted when the timestep was reduced "
        "to 0.0625 h, the number of cells was doubled and the roof length was changed (Sections 3.4 and 3.8), so they are not artefacts of "
        "discretisation. They arise from an identifiable mechanism that follows from the failure criterion, a retaining segment that stops snow "
        "released upslope. Their small nominal releases, however, depend on that segment holding close to its threshold and did not survive "
        "uncertainty (Section 3.6). Within the model's assumptions the intermediate states are therefore physical, but their release magnitudes "
        "are model-derived and threshold-sensitive.",
    )
    para(
        doc,
        "The approach complements rather than competes with CFD and melt models. CFD and wind-tunnel methods predict deposition and drift, and "
        "energy-balance models predict melt, liquid water and refreezing; neither is practical for the "
        f"{int(bud.objective_evaluations.sum()):,} design evaluations performed here. A combined workflow would use such models, or measurements, "
        "to generate roof-level snow input and melt, and a calibrated release model of the present kind to screen constructable configurations.",
    )
    para(
        doc,
        "The revised metric changes the interpretation of shedding roofs. Steep smooth roofs release often, and when releases are closely spaced they form "
        "long continuous events with large integrated mass; per-step metrics hid this by dividing each release among timesteps. Whether a series of "
        "small releases is less hazardous than one large release depends on occupancy below the eave, and the fixed-window metrics are supplied for "
        "that reason.",
    )
    para(
        doc,
        "For Japanese practice the result is a design option, not a compliance route. Retaining designs carry the full design snow load, and Article "
        f"86 withholds the slope reduction where sliding is prevented {c('JPR03')}. A graded roof that retains most snow should therefore be "
        "designed as a retention roof structurally, while its potential benefit is fewer clearing operations and smaller, more predictable eave releases.",
    )
    doc.add_heading("4.1 Implications for design practice and guidance", 2)
    para(
        doc,
        "Graded roofs could be built from conventional components: pitch changes as multi-pitch or curved rafters, and surface zones as different "
        "roofing finishes or retention elements. Constructability matters in two ways. Limits on segment length and transitions remove fine "
        "profiles that a continuous search would otherwise exploit, and each change of pitch or finish adds detailing, waterproofing and "
        "maintenance demands that the present rules represent only as counts. For guidance documents, the results point to foundational items "
        "rather than design rules: roof-snow treatment could be described by zones along the roof rather than by a single roof type; standard "
        "tests reporting static and kinetic friction and adhesion of roofing products across temperature and wetness would allow release "
        "thresholds to be estimated; and any roof whose segments retain snow should be treated as a retention roof in structural design, with "
        "the clear area below shedding zones specified. These are research needs for codes, not recommendations for current design.",
    )
    doc.add_heading("4.2 Limitations", 2)
    para(
        doc,
        "The model has not been calibrated or validated against roof-scale release measurements; friction, adhesion, ageing and near-melt laws are "
        "assumptions informed only qualitatively by interface studies. Slabs are rigid blocks; fracture, cornices, creep and glide, eave overhang, "
        "wind redistribution and three-dimensional flow are omitted. Meltwater and rain leave the roof immediately: liquid-water retention, refreezing, "
        "ice dams, runoff routing, drainage capacity and hydrologically triggered wet-snow releases are not represented, so rain-on-snow effects are "
        "limited to a melt-energy term and a near-melt friction reduction. Multi-scenario hydrological-triggering frameworks, such as that "
        f"developed for debris flows in small basins {c('LIU26')}, show how rainfall and meltwater scenarios can be coupled to failure analysis; a "
        "roof analogue would require liquid-water retention, drainage and wet-snow strength models and would be needed before application to "
        "climates dominated by rain-on-snow. Synthetic winters are stylised, and the JMA records are ground observations at stations, not "
        "roof-level climate; daily JMA data also cannot resolve sub-daily timing. The release magnitude attributed to shedding roofs depends on the event-separation time (Table 3), so comparisons of S_{event,max} "
        "are conditional on the pre-specified 1 h definition. Optimisation is heuristic and limited to a 2D strip with three surface classes. "
        "The uniform reference is exhaustive, whereas graded fronts are heuristic approximations from a fixed budget and may be incomplete; this "
        "asymmetry biases the comparison against grading rather than in its favour. Roof length was varied only between 4 and 12 m by "
        "re-evaluation, and other sizes, widths and roof shapes were not tested.",
    )
    doc.add_heading("4.3 Future validation", 2)
    para(
        doc,
        "Product-specific inclined-plane friction and adhesion tests across temperature and liquid-water content, instrumented roof panels with load "
        f"cells and time-lapse imaging such as the semi-full-scale setup of Tominaga et al. {c('CRST11')}, and eave-catchment measurements of release mass "
        "and timing are needed before graded designs can be recommended.",
    )
    doc.add_heading("5. Conclusions", 1)
    para(
        doc,
        "With a timestep-independent event metric and constructability enforced inside the search, constructable uniform roofs in this model "
        "either shed nearly all snow or retained all of it. Spatially graded roofs reproducibly filled this gap with intermediate "
        "retention-release combinations that survived numerical refinement and persisted under uncertainty, although with substantially larger "
        "releases, and they did not materially improve the overall frontier. The timestep sensitivity of the submitted version arose mainly from "
        "the per-step release metric and largely disappeared with the event metric; the loss of intermediate trade-offs after post hoc mapping "
        "arose from applying constructability after a continuous search and did not occur when the rules were enforced during the search. For "
        "passive snow management, grading offers a design option that needs no operating energy: a roof can be configured to hold most of its "
        "snow while limiting eave releases, but the size of those releases depends on interface properties that must be measured. Unlike CFD or "
        "melt models, the approach does not predict deposition or meltwater processes; its role is to screen constructable configurations for "
        "experimental testing, which remains necessary before any design recommendation.",
    )

    doc.add_heading("Declarations", 1)
    for k, t in (
        ("Funding: ", meta["funding"]),
        ("Declaration of competing interests: ", meta["competing_interests"]),
        (
            "Data and code availability: ",
            "Code, configuration, raw public-data snapshots, acquisition ledger with SHA-256 checksums, and all result tables are available in the project repository.",
        ),
        (
            "Declaration of generative AI and AI-assisted technologies in the manuscript preparation process: ",
            "During the preparation of this work, the author used Devin (Cognition AI) to support coding, data acquisition, analysis scripting and drafting. The author reviewed and edited the content and takes full responsibility for the publication.",
        ),
        ("CRediT authorship contribution statement: ", "REQUIRED - author confirmation of roles."),
    ):
        para(doc, t, bold_lead=k)

    doc.add_heading("References", 1)
    for n, rid in enumerate(ref.order, 1):
        para(doc, f"[{n}] {ref.text(rid)}")

    doc.add_heading("Tables", 1)
    t1 = c24.reset_index()[
        [
            "dt_h",
            "l_max_kg_per_m__agree_frac",
            "s_event_max_kg_per_m__agree_frac",
            "s_window_1h_kg_per_m__agree_frac",
            "total_shed_kg_per_m__agree_frac",
            "event_count_within1_frac",
            "s_event_max_kg_per_m__p95_rel",
            "acceptable",
        ]
    ]
    t1 = t1.sort_values("dt_h", ascending=False)
    t1.columns = [
        "dt (h)",
        "L_{max}",
        "S_{event,max}",
        "S_{1h,max}",
        "Total release",
        "Event count +/-1",
        "P95 rel. diff. S_{event,max}",
        "Acceptable",
    ]
    for col in t1.columns[1:6]:
        t1[col] = t1[col].map(lambda x: f"{x:.3f}")
    t1["P95 rel. diff. S_{event,max}"] = t1["P95 rel. diff. S_{event,max}"].map(
        lambda x: f"{100 * float(x):.2f}%"
    )
    table(
        doc,
        t1,
        "Table 1. Fraction of design-winter pairs within tolerance of the dt = 0.0625 h, 24-cell reference.",
    )
    t2 = fs.reset_index()[
        [
            "set",
            "unique_objective_pairs",
            "nondominated_designs_incl_ties",
            "hv_max_x1.05",
            "hv_max_x1.1",
            "hv_max_x1.5",
            "eps_norm_uniform_to_set",
            "matched_s_improvement_median",
            "graded_pairs_on_front",
        ]
    ]
    t2.columns = [
        "Set",
        "Unique pairs",
        "Nondominated designs",
        "HV (1.05)",
        "HV (1.1)",
        "HV (1.5)",
        "Epsilon uniform to set",
        "Median matched S gain",
        "Graded pairs",
    ]
    for col in t2.columns[3:8]:
        t2[col] = t2[col].map(lambda x: f"{x:.4f}")
    table(doc, t2, "Table 2. Constructable front comparison (5 seeds pooled for graded sets).")
    t3 = evs.reset_index()[
        [
            "variant",
            "uniform_front_pairs",
            "combined_front_pairs",
            "uniform_gap_lo",
            "pairs_in_uniform_gap",
            "gap_s_event_max",
            "eps_uniform_to_combined",
        ]
    ]
    t3.columns = [
        "Variant",
        "Uniform front pairs",
        "Combined front pairs",
        "Uniform gap starts at L_{max} (kg m^{-1})",
        "Graded pairs in gap",
        "Largest S_{event,max} in gap (kg m^{-1})",
        "Epsilon uniform to combined (kg m^{-1})",
    ]
    for col in t3.columns[3:]:
        if col != "Graded pairs in gap":
            t3[col] = t3[col].map(f1)
    table(doc, t3, "Table 3. Sensitivity to event-definition and entrainment choices.")

    doc.add_heading("Figure captions", 1)
    caps = [
        "Figure 1. (a) Example constructable graded profile coloured by surface class. (b) Eave outflow per 1-h step in the maritime warming winter with physical events shaded. (c) Research workflow.",
        "Figure 2. Weather forcing. Synthetic winters: (a) snowfall rate, (b) air temperature and (c) rain rate. JMA station-winters (scenario forcing only): (d) daily mean air temperature, (e) daily precipitation and (f) cumulative precipitation from 1 November.",
        "Figure 3. (a) Median ratio of release endpoints to the dt = 0.0625 h reference. (b) Fraction of design-winter pairs within the pre-specified tolerance; dashed line is the 95% criterion.",
        "Figure 4. Constructable Pareto fronts for uniform, geometry-only, surface-only and joint sets: (a) full range, (b) intermediate region between the uniform shedding and retention regimes.",
        "Figure 5. Slope profiles of representative intermediate graded designs; bar colours denote surface class.",
        "Figure 6. Normalised hypervolume after 15, 30 and 45 generations for each seed; dashed line is the exhaustive uniform set.",
        "Figure 7. Nominal versus Q95 outcomes under 250 common uncertainty draws for all nondominated designs.",
        "Figure 8. Objective pairs of uniform and nondominated graded designs under observed JMA station-winters (daily totals spread uniformly over 24 h).",
    ]
    for cap in caps:
        para(doc, cap)
    place_inline(doc, caps)
    for cp in doc.paragraphs:
        if re.match(r"(Figure|Table) \d+\.", cp.text):
            for r in cp.runs:
                r.font.size = Pt(10)
    OUT.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    return {"refs": ref.order}


if __name__ == "__main__":
    info = build(OUT / "manuscript_R1_clean.docx")
    print(json.dumps(info))
