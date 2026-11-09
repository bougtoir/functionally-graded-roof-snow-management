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
        b = pd.read_csv("references/references_r1_additional.csv")
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
            r.font.size = Pt(7)
    for row in frame.itertuples(index=False):
        cells = t.add_row().cells
        for i, x in enumerate(row):
            cells[i].text = ""
            _runs(cells[i].paragraphs[0], str(x))
            for r in cells[i].paragraphs[0].runs:
                r.font.size = Pt(7)


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
        anchor._p.addnext(img._p)
        img._p.addnext(cp._p)


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
    fc = v["fc"]
    inter = fc[(fc[O[0]] > lo) & (fc[O[0]] < hi)]
    rob_i = rob[rob.segments.isin(inter.segments)]
    rob_u = rob[~rob.graded]
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
    uc = v["ucont"]
    wx = v["wx"]
    diag = v["diag"]
    evs = v["evs"]
    hv_last = v["seedhv"][v["seedhv"].generation == v["seedhv"].generation.max()]

    doc = Document()
    st = doc.styles
    st["Normal"].font.name = "Arial"
    st["Normal"].font.size = Pt(10)
    for s in ("Title", "Heading 1", "Heading 2", "Heading 3"):
        st[s].font.name = "Arial"
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
        "Roofs in heavy-snowfall regions either retain snow, which raises structural load and the need for manual "
        "clearing, or shed it, which creates eave-release hazards. We asked whether spatial grading of slope and "
        "surface class along a constructable roof creates retention-release trade-offs that uniform roofs cannot provide. "
        "A reduced-order ridge-to-eave model with Coulomb-adhesion failure, exact threshold-crossing times and work-energy "
        "runout was forced by three synthetic winters. Release hazard was quantified by a pre-specified physical event "
        "metric, the largest integrated eave-release mass per event (S_{event,max}), replacing a per-timestep metric that "
        "halved whenever the timestep halved. Numerical convergence was tested on "
        f"{int(conv.pairs.iloc[0])} design-winter pairs; every tested timestep met the pre-specified criterion. "
        "Constructability (segments of at least 3 cells, at most 6 transitions, integer slopes, three discrete surface "
        "classes) was enforced inside NSGA-II by a feasible encoding, and graded searches were compared with all "
        f"{len(pd.read_csv(R / 'optimization/uniform_constructable_evaluated.csv'))} constructable uniform roofs. "
        f"Uniform roofs either shed nearly all snow (maximum retained mass L_{{max}} {f1(lo)} kg m^{{-1}}) or retained all of it "
        f"({f0(hi)} kg m^{{-1}}). Graded roofs added {int(gj.pairs_in_uniform_gap)} nondominated intermediate combinations "
        f"(S_{{event,max}} {f1(gj.S_min)}-{f1(gj.S_max)} kg m^{{-1}}), found in all {len(seeds)} optimisation runs, but changed "
        f"normalised hypervolume only from {fs.loc['uniform', 'hv_max_x1.1']:.3f} to {fs.loc['joint', 'hv_max_x1.1']:.3f}. "
        "Spatial grading is therefore a configurable means of intermediate retention rather than a general improvement; "
        "the model is verified numerically but not validated against roof observations.",
    )
    doc.add_paragraph(
        "Keywords: roof snow; snow shedding; snow retention; heavy-snowfall areas; constructability; multiobjective optimisation; reduced-order model"
    )

    doc.add_heading("1. Introduction", 1)
    para(
        doc,
        f"Heavy snowfall shapes building practice across much of Japan. Under the Act on Special Measures for Heavy Snowfall Areas {c('JPR04')}, "
        f"{jp.loc[1, 'value']} municipalities are designated heavy-snowfall areas, covering {jp.loc[3, 'value']}% of the national land and "
        f"about {jp.loc[4, 'value'].split(' (')[1].rstrip(')')} of the population {c('JPR01')}. Snow-related deaths numbered {jp.loc[7, 'value']} in the "
        f"FY2023 winter; over the preceding decade about {jp.loc[8, 'value']}% occurred during snow removal and about {jp.loc[9, 'value']}% "
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
        f"practice {c('JP01', 'JP10')}, not in binding rules. The model in this paper does not compute code snow loads and makes no compliance claim.",
    )
    para(
        doc,
        f"Roof-snow research has concentrated on drift and deposition {c('CRST01', 'CRST02', 'CRST03', 'CRST04', 'CRST05', 'CRST06', 'CRST08', 'CRST09', 'JP08')} "
        f"and on load monitoring {c('CRST11')}. Sliding depends on surface roughness, water content, ageing and adhesion {c('JP05', 'JP06', 'CRST12')}, "
        f"snow guards change retention {c('JP04')}, and melting systems trade energy for clearance {c('JP07', 'CRST10')}; sliding models for inclined "
        f"photovoltaic panels show the sensitivity of release to interface parameters {c('CRST07')}. Municipal guidance highlights the hazard of "
        f"falling roof snow and ice {c('JP09')}. Whether varying slope and surface along a single roof can place it between the retention and "
        "shedding extremes has not, to our knowledge, been examined under explicit constructability limits.",
    )
    para(
        doc,
        "The question tested here was whether spatial grading produces physically interpretable, numerically stable, robust and constructable "
        "retention-release trade-offs that uniform roofs cannot provide. A negative or limited answer was admissible. Compared with the originally "
        "submitted analysis, the release metric, the transport scheme, the treatment of constructability and the number of optimisation seeds were "
        "revised; all changes are listed in Section 2.8 and the original outputs are retained.",
    )

    doc.add_heading("2. Methods", 1)
    doc.add_heading("2.1 Reduced-order roof-snow model", 2)
    rf = cfg["roof"]
    para(
        doc,
        f"A {rf['length_m']:.0f} m ridge-to-eave strip of unit width was divided into {rf['cells']} cells, each with slope, static and kinetic "
        "friction and adhesion. Snowfall was added as mass, compacted with age, melted by a degree-hour factor plus a rain-heat term, and "
        "assigned a dynamic friction that increased with age and decreased near melting (parameters in Supplementary Table S1). "
        "A cell with mass m per unit area failed when gravity exceeded the Coulomb-adhesion resistance:",
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
        number="1",
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
        number="2",
    )
    para(
        doc,
        "and it stops where the speed reaches zero or leaves at the eave. Mass resting in cells it crosses that are themselves at or above threshold is "
        "entrained inelastically. Cells that cannot hold any snow (sin θ > μ_{s} cos θ and c = 0) route incoming snowfall continuously to the eave or "
        "to the first retaining cell. Mass balance (input = eave release + melt + residual) was checked in every run.",
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
        number="3",
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
        "as supplementary scenarios, spreading daily totals uniformly over 24 h. These ground observations are not roof-snow validation data.",
    )
    doc.add_heading("2.4 Numerical verification", 2)
    para(
        doc,
        "Before optimisation, all constructable uniform roofs and 60 random constructable graded roofs were simulated at dt = 1, 0.5, 0.25, 0.125 "
        "and 0.0625 h (reference) with 24 cells, and at 48 and 96 cells. A timestep was acceptable if at least 95% of pairs agreed with the "
        "reference within max(2%, 1 kg m^{-1}) for L_{max}, S_{event,max}, S_{1h,max} and total release, at least 90% had event counts within one, "
        "and mass-balance error was below 10^{-6} kg m^{-1}; the coarsest acceptable step was used. All final nondominated designs were then "
        "re-evaluated at 0.0625 h and at 48 cells.",
    )
    doc.add_heading("2.5 Constructable optimisation", 2)
    para(
        doc,
        "Candidates were decoded from a unit hypercube into piecewise-constant segments that satisfy every rule by construction: segments of at "
        f"least {rf['minimum_segment_cells']} cells, at most {rf['maximum_transitions']} transitions, integer slopes {rf['slope_bounds_deg'][0]}-{rf['slope_bounds_deg'][1]} degrees, "
        f"adjacent slope changes of at most {rf['adjacent_slope_limit_deg']} degrees, and one of three surface classes (smooth metal, aged coated metal, "
        "rough retention surface). Geometry-only (single class), surface-only (single slope) and joint searches each used NSGA-II with population "
        f"{cfg['optimizer']['population']}, {cfg['optimizer']['generations']} generations and {diag.seed.nunique()} seeds. The uniform reference was the exhaustive "
        "set of constructable uniform roofs; a 6,300-design continuous uniform grid was evaluated as a sensitivity.",
    )
    doc.add_heading("2.6 Frontier comparison", 2)
    para(
        doc,
        "Fronts were compared by normalised hypervolume (reference point 1.1 times the largest observed objectives, with 1.05 and 1.5 as "
        "sensitivities), additive epsilon in both directions, matched-objective improvement, unique objective pairs, per-seed variability and "
        "hypervolume after 15, 30 and 45 generations. The number of graded pairs lying inside the L_{max} gap of the uniform front is reported "
        "as a descriptive summary defined after the fronts were inspected.",
    )
    doc.add_heading("2.7 Robustness and event-definition sensitivity", 2)
    rb = cfg["robustness"]
    cv = rb["coefficient_of_variation"]
    para(
        doc,
        f"Every nondominated design was simulated under {rb['samples']} common random draws (seed {rb['seed']}) of lognormal multipliers on friction "
        f"(CV {cv['friction']}), adhesion ({cv['adhesion']}), fresh-snow density ({cv['fresh_snow_density']}) and snowfall ({cv['snowfall']}), and a normal "
        f"temperature offset (SD {cv['temperature_sd_c']} degrees C); the {int(100 * rb['robust_quantile'])}th percentiles (Q95) are reported. The event definition was "
        "varied (separation 10 min and 3 h; activity threshold 0.1 and 10 kg m^{-1} h^{-1}) and entrainment was switched off.",
    )
    doc.add_heading("2.8 Changes from the submitted analysis and reproducibility", 2)
    para(
        doc,
        "The submitted analysis moved snow one cell per step and defined events per timestep, so its release endpoint depended on dt; it also "
        "applied constructability only after optimisation. The revision replaced transport, the release metric and the constraint handling, "
        "increased seeds from three to five, and selected dt by the rule above. Code, configuration, raw public-data snapshots with checksums, "
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
    para(
        doc,
        "Across the event-definition and entrainment variants, the number of graded designs on the combined front ranged from "
        f"{int(evs.graded_designs_on_combined_front.min())} to {int(evs.graded_designs_on_combined_front.max())} and the uniform-to-combined epsilon from "
        f"{f1(evs.eps_uniform_to_combined.min())} to {f1(evs.eps_uniform_to_combined.max())} kg m^{{-1}} (Table 3).",
    )
    doc.add_heading("3.6 Robustness", 2)
    para(
        doc,
        f"Under parameter and forcing uncertainty, the Q95 L_{{max}} of the intermediate graded designs ranged from {f0(rob_i.l_q.min())} to {f0(rob_i.l_q.max())} kg m^{{-1}} "
        f"and their Q95 S_{{event,max}} from {f1(rob_i.s_q.min())} to {f0(rob_i.s_q.max())} kg m^{{-1}}, compared with nominal S_{{event,max}} of {f1(gj.S_min)}-{f1(gj.S_max)} kg m^{{-1}} (Fig. 7). "
        f"For uniform front designs, Q95 S_{{event,max}} ranged from {f1(rob_u.s_q.min())} to {f0(rob_u.s_q.max())} kg m^{{-1}}. "
        f"{int((rob_i.s_q < lo).sum())} of {len(rob_i)} intermediate graded designs kept Q95 S_{{event,max}} below the nominal release of the most retentive "
        f"shedding uniform roof ({f1(lo)} kg m^{{-1}}).",
    )
    doc.add_heading("3.7 JMA station-winter scenarios", 2)
    para(
        doc,
        f"Under the {sw} observed station-winters (snowfall water equivalent {f0(v['jmaf'].snowfall_we_kg_m2.min())}-{f0(v['jmaf'].snowfall_we_kg_m2.max())} kg m^{{-2}}), "
        "the same designs were re-simulated without re-optimisation (Fig. 8). "
        f"These scenario results extend the comparison to longer, observed forcing but do not validate roof behaviour.",
    )

    doc.add_heading("4. Discussion", 1)
    para(
        doc,
        "Within this model, spatial grading did not produce a generally better roof: hypervolume, epsilon and matched-objective gains over the "
        "exhaustive constructable uniform set were small. What grading did provide, reproducibly across seeds, was access to intermediate states between "
        "near-complete shedding and full retention, where a roof holds most of its snow but releases it in small events. Uniform roofs reach these "
        "states only through non-catalogue surface properties, if at all. In practice this corresponds to a retention zone combined with a short "
        "controlled-shedding eave zone, a configuration related to snow guards and retention roofs in regional guidance "
        f"{c('JP02', 'JP03', 'JP04')}; the mechanism is physically interpretable (upslope releases stop on a retaining segment).",
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
    doc.add_heading("4.1 Limitations", 2)
    para(
        doc,
        "The model has not been calibrated or validated against roof-scale release measurements; friction, adhesion, ageing and near-melt laws are "
        "assumptions informed only qualitatively by interface studies. Slabs are rigid blocks; fracture, cornices, creep and glide, eave overhang, "
        "wind redistribution and three-dimensional flow are omitted. Meltwater and rain leave the roof immediately: liquid-water retention, refreezing, "
        "ice dams, runoff routing, drainage capacity and hydrologically triggered wet-snow releases are not represented, so rain-on-snow effects are "
        "limited to a melt-energy term and a near-melt friction reduction. Synthetic winters are stylised, and daily JMA data cannot resolve "
        "sub-daily timing. Optimisation is heuristic and limited to a 2D strip with three surface classes.",
    )
    doc.add_heading("4.2 Future validation", 2)
    para(
        doc,
        "Product-specific inclined-plane friction and adhesion tests across temperature and liquid-water content, instrumented roof panels with load "
        f"cells and time-lapse imaging such as the semi-full-scale setup of Tominaga et al. {c('CRST11')}, and eave-catchment measurements of release mass "
        "and timing are needed before graded designs can be recommended.",
    )
    doc.add_heading("5. Conclusions", 1)
    para(
        doc,
        "With a timestep-independent event metric and constructability enforced inside the search, constructable uniform roofs either shed nearly all "
        "snow or retained all of it. Spatially graded roofs reproducibly filled this gap with intermediate retention-release combinations but did not "
        "materially improve the overall frontier. Spatial grading is best viewed as a configurable retention strategy whose physical benefit remains to "
        "be demonstrated experimentally.",
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
            "uniform_front_size",
            "combined_front_size",
            "eps_uniform_to_combined",
            "graded_designs_on_combined_front",
        ]
    ]
    t3.columns = [
        "Variant",
        "Uniform front pairs",
        "Combined front pairs",
        "Epsilon uniform to combined (kg m^{-1})",
        "Graded designs on combined front",
    ]
    t3["Epsilon uniform to combined (kg m^{-1})"] = t3[
        "Epsilon uniform to combined (kg m^{-1})"
    ].map(f1)
    table(doc, t3, "Table 3. Sensitivity to event-definition and entrainment choices.")

    doc.add_heading("Figure captions", 1)
    caps = [
        "Figure 1. (a) Example constructable graded profile coloured by surface class. (b) Eave outflow per 1-h step in the maritime warming winter with physical events shaded.",
        "Figure 2. Synthetic forcing: snowfall rate and air temperature for the three winters.",
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
    OUT.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    return {"refs": ref.order}


if __name__ == "__main__":
    info = build(OUT / "manuscript_R1_clean.docx")
    print(json.dumps(info))
