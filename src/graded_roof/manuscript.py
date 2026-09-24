from __future__ import annotations

import csv
import json
import zipfile
from copy import deepcopy
from pathlib import Path

import pandas as pd
import yaml
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from PIL import Image
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches as PptxInches
from pptx.util import Pt as PptxPt

TITLE = (
    "Functionally graded roofs for passive snow management: "
    "a reduced-order multiobjective modeling study"
)

FIGURE_CAPTIONS = [
    "Figure 1. Reduced-order model and comparative optimization workflow.",
    "Figure 2. Synthetic snowfall scenarios and JMA ground-snow contexts.",
    "Figure 3. Primary modeled retained-mass and release-mass Pareto comparison.",
    "Figure 4. Selected graded joint profile and generic mapped surface classes.",
    "Figure 5. Geometry-only, surface-only, and joint heterogeneous Pareto fronts.",
    "Figure 6. Numerical convergence relative to the finest tested resolution.",
    "Figure 7. Prespecified one-at-a-time sensitivity of primary outcomes.",
    "Figure 8. Monte Carlo perturbation distributions for frontier candidates.",
    "Figure 9. Labor-scarcity selections and frozen strategy classifications.",
]

FIGURE_FILENAMES = [
    "figure_1_conceptual_model.png",
    "figure_2_weather_scenarios.png",
    "figure_3_primary_pareto_comparison.png",
    "figure_4_selected_graded_profile.png",
    "figure_5_ablation_pareto_fronts.png",
    "figure_6_numerical_convergence.png",
    "figure_7_sensitivity.png",
    "figure_8_monte_carlo_robustness.png",
    "figure_9_decision_phase_diagram.png",
]


def _format_number(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.1f}"
    if abs(value) >= 10:
        return f"{value:.2f}"
    return f"{value:.3f}"


def _add_line_numbering(document: Document) -> None:
    for section in document.sections:
        line_number = OxmlElement("w:lnNumType")
        line_number.set(qn("w:countBy"), "1")
        line_number.set(qn("w:start"), "1")
        line_number.set(qn("w:restart"), "continuous")
        section._sectPr.append(line_number)


def _configure_document(document: Document) -> None:
    styles = document.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)
    for style_name in ["Title", "Heading 1", "Heading 2", "Heading 3"]:
        styles[style_name].font.name = "Arial"
    for section in document.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.start_type = WD_SECTION.CONTINUOUS
    _add_line_numbering(document)


def _add_equation(document: Document, equation: str) -> None:
    paragraph = document.add_paragraph()
    math_paragraph = OxmlElement("m:oMathPara")
    math = OxmlElement("m:oMath")
    run = OxmlElement("m:r")
    text = OxmlElement("m:t")
    text.text = equation
    run.append(text)
    math.append(run)
    math_paragraph.append(math)
    paragraph._p.append(math_paragraph)


def _enforce_ascii(document: Document) -> None:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2212": "-",
        "\u00d7": "x",
        "\u2264": "<=",
        "\u2022": "-",
    }
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            text = run.text
            for original, replacement in replacements.items():
                text = text.replace(original, replacement)
            text.encode("ascii")
            if text != run.text:
                run.text = text
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        text = run.text
                        for original, replacement in replacements.items():
                            text = text.replace(original, replacement)
                        text.encode("ascii")
                        if text != run.text:
                            run.text = text


def _add_title_page(document: Document, metadata: dict) -> None:
    title = document.add_paragraph()
    title.style = document.styles["Title"]
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run(TITLE)
    for author in metadata["authors"]:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run(author["name"])
        if author.get("corresponding"):
            paragraph.add_run("*")
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run(author["affiliation"])
    corresponding = next(
        author for author in metadata["authors"] if author.get("corresponding")
    )
    document.add_paragraph(
        "Corresponding author: "
        f"{corresponding['name']}, {corresponding['postal_address']}, "
        f"{corresponding['email']}"
    )


def _add_keywords(document: Document) -> None:
    document.add_paragraph(
        "Keywords: roof snow; passive snow management; multiobjective optimization; "
        "spatial heterogeneity; snow shedding; reduced-order model"
    )


def _add_dataframe_table(
    document: Document,
    frame: pd.DataFrame,
    caption: str,
    columns: list[str],
    *,
    maximum_rows: int | None = None,
    headers: list[str] | None = None,
) -> None:
    document.add_paragraph(caption, style="Heading 3")
    shown = frame.loc[:, columns]
    if maximum_rows is not None:
        shown = shown.head(maximum_rows)
    table = document.add_table(rows=1, cols=len(columns))
    table.style = "Table Grid"
    for index, column in enumerate(columns):
        cell = table.rows[0].cells[index]
        cell.text = (
            headers[index] if headers is not None else column
        )
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.size = Pt(7)
    for row in shown.itertuples(index=False, name=None):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            if isinstance(value, float):
                cells[index].text = _format_number(value)
            else:
                cells[index].text = str(value)
            for run in cells[index].paragraphs[0].runs:
                run.font.size = Pt(7)


def _reference_text(row: pd.Series) -> str:
    authors = str(row["authors"]).replace(";", ",")
    identifier = row["doi_or_identifier"]
    doi = (
        f" https://doi.org/{identifier}."
        if str(identifier).startswith("10.")
        else f" {identifier}."
    )
    return (
        f"{authors}. {row['title']}. {row['journal_or_publisher']}. "
        f"{int(row['year'])}.{doi}"
    )


def _result_sentence(
    uniform: pd.Series,
    joint: pd.Series,
) -> str:
    l_change = (
        100.0
        * (joint["l_max_kg_per_m"] - uniform["l_max_kg_per_m"])
        / max(abs(float(uniform["l_max_kg_per_m"])), 1e-12)
    )
    s_change = (
        100.0
        * (joint["s_max_kg_per_m"] - uniform["s_max_kg_per_m"])
        / max(abs(float(uniform["s_max_kg_per_m"])), 1e-12)
    )
    return (
        "At the normalized-distance knee, the selected joint profile had "
        f"Lmax={_format_number(joint['l_max_kg_per_m'])} kg m−1 and "
        f"Smax={_format_number(joint['s_max_kg_per_m'])} kg m−1. "
        "Relative to the selected uniform knee, these values changed by "
        f"{l_change:+.1f}% and {s_change:+.1f}%, respectively. "
        "This knee comparison is illustrative and does not establish front-wide "
        "superiority."
    )


def build_manuscript(root: Path) -> Path:
    results = root / "results" / "generated"
    tables = root / "tables" / "generated"
    metadata = yaml.safe_load(
        (root / "manuscript" / "author_metadata.yaml").read_text(encoding="utf-8")
    )
    config = yaml.safe_load(
        (root / "config" / "production.yaml").read_text(encoding="utf-8")
    )
    baseline = pd.read_csv(results / "baseline_aggregate.csv")
    convergence = pd.read_csv(results / "convergence.csv")
    uniform_front = pd.read_csv(results / "uniform_pareto.csv")
    joint_front = pd.read_csv(results / "joint_pareto.csv")
    table_1 = pd.read_csv(tables / "table_1_pareto_summary.csv")
    table_2 = pd.read_csv(tables / "table_2_selected_profile.csv")
    table_3 = pd.read_csv(tables / "table_3_discretization.csv")
    table_5 = pd.read_csv(tables / "table_5_labor_scarcity.csv")
    table_6 = pd.read_csv(tables / "table_6_complexity_analysis.csv")
    table_7 = pd.read_csv(tables / "table_7_complexity_penalty.csv")
    table_8 = pd.read_csv(tables / "table_8_robustness_summary.csv")
    references = pd.read_csv(root / "references" / "literature_database.csv")

    def knee(frame: pd.DataFrame) -> pd.Series:
        objectives = frame[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy(float)
        spans = objectives.max(axis=0) - objectives.min(axis=0)
        normalized = (objectives - objectives.min(axis=0)) / spans.clip(min=1e-12)
        return frame.iloc[int((normalized**2).sum(axis=1).argmin())]

    uniform_knee = knee(uniform_front)
    joint_knee = knee(joint_front)
    accepted = convergence[convergence["within_tolerance"]]
    convergence_text = (
        f"The frozen {100 * config['convergence']['relative_tolerance']:.0f}% "
        "four-metric convergence tolerance was met by "
        f"{len(accepted)} of {len(convergence)} tested resolution combinations."
    )
    retention = baseline.loc[
        baseline["design"] == "retention_non_shedding"
    ].iloc[0]
    shedding = baseline.loc[
        baseline["design"] == "conventional_shedding"
    ].iloc[0]

    document = Document()
    _configure_document(document)
    _add_title_page(document, metadata)
    document.add_heading("Abstract", level=1)
    abstract = (
        "Passive roof-snow strategies face a modeled trade-off between retaining "
        "snow mass and releasing large discrete snow-shedding events. This study "
        "tests whether spatial variation in roof slope and snow-surface interaction "
        "changes that trade-off relative to optimized spatially uniform roofs. A "
        "unit-width roof was discretized into cells with slope, static and kinetic "
        "friction, adhesion, snow mass, age, volume, and density states. Synthetic "
        "weather scenarios were used for primary optimization; official Japanese "
        "Meteorological Agency daily observations provided supplementary scenario "
        "evaluation rather than validation. Uniform designs were mapped before "
        "checkpointed, multi-seed NSGA-II optimization of geometry-only, surface-only, "
        "and joint heterogeneous profiles. Primary outcomes were maximum modeled roof "
        "snow mass per metre and maximum eave-release mass per timestep. Convergence, "
        "ablation, parameter sensitivity, Monte Carlo perturbation, continuous-to-"
        "discrete surface mapping, and labor-scarcity decision weights were evaluated. "
        + _result_sentence(uniform_knee, joint_knee)
        + " The results define conditional modeled trade-offs, not structural or "
        "pedestrian safety. The reduced-order model omits wind redistribution and "
        "requires calibration against roof-scale observations before design use."
    )
    document.add_paragraph(abstract)
    _add_keywords(document)

    document.add_heading("1. Introduction", level=1)
    document.add_paragraph(
        "Roof snow is spatially variable, evolves with weather, and can either remain "
        "on the roof or leave in discrete releases. Roof-scale experiments and "
        "deposition studies show that geometry, wind, and scale influence snow "
        "distributions, while validation remains essential for computational models "
        "[1–6]. Adjacent photovoltaic, membrane-roof, meteorological, and field studies "
        "further motivate explicit sensitivity analysis and independent validation "
        "[7–12]."
    )
    document.add_paragraph(
        "Japanese technical and administrative sources distinguish retention, "
        "shedding, melting, and load-resisting strategies and document the importance "
        "of surface condition, aging, snow guards, drainage, cornices, and site context "
        "[13–21]. These sources do not establish universal material coefficients or "
        "safety thresholds. They instead motivate the present comparison of generic "
        "spatially uniform and graded design spaces."
    )
    document.add_paragraph(
        "The research question was frozen before production analysis: under identical "
        "modeled environmental conditions, how does allowing spatial variation in roof "
        "geometry and snow-surface interaction change the achievable trade-off between "
        "retained modeled snow mass and discrete shedding events compared with optimized "
        "uniform roofs? The hypothesis that heterogeneity expands the attainable design "
        "space was tested without assuming superiority."
    )

    document.add_heading("2. Methods", level=1)
    document.add_heading("2.1 Reduced-order roof-snow model", level=2)
    document.add_paragraph(
        f"An {config['roof']['length_m']:g} m long, "
        f"{config['roof']['width_m']:g} m wide roof was represented by "
        f"{config['roof']['cells']} ridge-to-eave cells. Each "
        "cell carried slope, static friction, kinetic friction, adhesion, snow mass, "
        "mass-weighted age, volume, and density. Snowfall was added before each "
        "within-step maximum was recorded. Melt removed mass, volume, and age moment "
        "proportionally. Compaction changed volume and diagnostic depth. Density "
        "converted observed snowfall depth to mass but was not asserted to change "
        "basal sliding at fixed mass."
    )
    document.add_paragraph(
        "A cell became mobile when downslope gravity exceeded static friction plus "
        "area-scaled adhesion. Kinetic friction controlled transport after release. "
        "Mass, age moment, and volume moved together. Snow leaving the final cell was "
        "an eave-shedding event. The kinetic-energy metric was a roof-wide specific-"
        "energy proxy, not an impact or injury model."
    )
    _add_equation(document, "F_g = m g sin(theta)")
    _add_equation(document, "F_r = mu_s m g cos(theta) + A tau_a")
    document.add_heading("2.2 Outcomes and comparison sets", level=2)
    document.add_paragraph(
        "The locked primary outcomes were Lmax, the maximum modeled roof snow mass "
        "per metre width immediately after snowfall and before same-step melt or "
        "release, and Smax, the maximum eave-release mass in one timestep per metre "
        "width. Secondary outcomes included total shed mass, event count, event-mass "
        "summaries, Snow Shedding Concentration Index (SSCI), kinetic-energy proxy, "
        "intervention-threshold time, manual triggers, residual mass, maximum modeled "
        "snow depth, total variation, transition count, and discretization loss."
    )
    _add_equation(document, "SSCI = sum_j (m_j / M_total)^2")
    document.add_paragraph(
        "Comparators were retention-oriented, shedding-oriented, and intermediate "
        "uniform baselines; the complete optimized uniform frontier; and geometry-only, "
        "surface-only, and joint heterogeneous frontiers. Figure 1 summarizes the "
        "model and optimization workflow; Figure 2 summarizes synthetic and observed "
        "weather contexts; Figures 3–5 show the primary frontier, selected profile, "
        "and ablation frontiers. Tables 1–3 report frontier metrics, the selected "
        "profile, and continuous-to-discrete mapping."
    )
    document.add_heading("2.3 Weather forcing", level=2)
    document.add_paragraph(
        f"Primary optimization used "
        f"{len(config['synthetic_weather']['scenarios'])} deterministic synthetic "
        "winters spanning cold "
        "persistent, maritime warming, and severe inland conditions, including repeated "
        "snowfall and configured rain-on-snow periods. JMA daily mean temperature, "
        "precipitation, snowfall depth, and ground snow depth were downloaded as "
        "immutable official HTML snapshots for "
        f"{len(config['jma']['stations'])} stations and "
        f"{len(config['jma']['winters'])} "
        "winters. Original value strings and parsed numeric fields were retained. "
        "JMA ground observations were used only as scenario forcing and were not treated "
        "as direct roof-load measurements."
    )
    document.add_heading("2.4 Optimization and analysis", level=2)
    document.add_paragraph(
        f"A full {config['optimizer']['uniform_slope_grid']} x "
        f"{config['optimizer']['uniform_friction_grid']} x "
        f"{config['optimizer']['uniform_adhesion_grid']} uniform "
        "slope-friction-adhesion map preceded "
        "heterogeneous optimization. Geometry-only, surface-only, and joint profiles "
        f"were parameterized by {config['optimizer']['profile_control_points']} "
        "control points interpolated across the roof. Checkpointed NSGA-II used a "
        f"population of {config['optimizer']['population']}, "
        f"{config['optimizer']['generations']} generations, and seeds "
        + ", ".join(str(seed) for seed in config["optimizer"]["seeds"])
        + ". Feasible historical evaluations from every seed were combined "
        "and filtered to complete nondominated sets. Normalized hypervolume, additive "
        "epsilon versus the uniform front, combined-set dominance, and matched-objective "
        "improvement were calculated. Per-seed hypervolume and additive epsilon "
        "summarized optimizer stochasticity in a machine-readable supplement. "
        "Figure 6 reports numerical "
        "convergence; Figure 7 reports prespecified one-at-a-time sensitivity."
    )
    document.add_paragraph(
        f"Monte Carlo robustness used {config['robustness']['samples']} deterministic "
        "draws perturbing friction, adhesion, fresh-snow density, snowfall, and "
        "temperature for prespecified candidates sampled across the uniform and joint "
        "fronts. Continuous joint profiles were mapped to "
        f"{len(config['surface']['discrete_classes'])} generic "
        "surface classes and piecewise roof segments of at least "
        f"{config['roof']['minimum_segment_cells']} cells, with at most "
        f"{config['roof']['maximum_transitions']} transitions, without claiming "
        "proprietary material performance. Frozen "
        "manual-intervention weights generated low, medium, and high labor-scarcity "
        "choices across configured snowfall, shedding-penalty, and allowable-release "
        "scenarios. Figures 8-9 and Tables 4-8 summarize these analyses."
    )

    document.add_heading("3. Results", level=1)
    document.add_heading("3.1 Baselines and convergence", level=2)
    document.add_paragraph(
        "Across the synthetic scenarios, the retention baseline produced "
        f"Lmax={_format_number(retention['l_max_kg_per_m'])} kg m−1 and "
        f"Smax={_format_number(retention['s_max_kg_per_m'])} kg m−1, whereas "
        "the shedding baseline produced "
        f"Lmax={_format_number(shedding['l_max_kg_per_m'])} kg m−1 and "
        f"Smax={_format_number(shedding['s_max_kg_per_m'])} kg m−1. "
        "These are modeled unit-width masses, not structural loads. "
        + convergence_text
        + " The kinetic-energy proxy was invariant to cell count for the uniform "
        "regression case."
    )
    document.add_heading("3.2 Uniform and heterogeneous Pareto sets", level=2)
    document.add_paragraph(_result_sentence(uniform_knee, joint_knee))
    summary_parts = []
    for row in table_1.itertuples(index=False):
        summary_parts.append(
            f"{row.design_class}: {int(row.pareto_designs)} points, "
            f"normalized hypervolume {_format_number(row.normalized_hypervolume)}, "
            "additive epsilon versus uniform "
            f"{_format_number(row.additive_epsilon_vs_uniform)}"
        )
    document.add_paragraph(
        "The complete frontier summary was " + "; ".join(summary_parts) + ". "
        "Because repeated objective pairs can correspond to distinct design profiles, "
        "all nondominated design rows were retained in machine-readable results."
    )
    document.add_heading("3.3 Robustness, complexity, and decision scenarios", level=2)
    robustness = pd.read_csv(results / "robustness.csv")
    robustness_summary = pd.read_csv(results / "robustness_summary.csv")
    robust_text = []
    for design_class, group in robustness.groupby("design_class"):
        robust_text.append(
            f"{design_class}: median Lmax "
            f"{_format_number(group['l_max_kg_per_m'].median())} kg m−1 and median "
            f"Smax {_format_number(group['s_max_kg_per_m'].median())} kg m−1"
        )
    document.add_paragraph(
        "Under the prespecified perturbation model, " + "; ".join(robust_text) + ". "
        "These distributions quantify parameter perturbations around selected designs "
        "and are not empirical confidence intervals."
    )
    robust_selected = robustness_summary.loc[
        robustness_summary["robust_selected"]
    ].iloc[0]
    nominal_knees = robustness_summary.loc[robustness_summary["nominal_knee"]]
    document.add_paragraph(
        "Among the prespecified frontier candidates, the robust selection was "
        f"{robust_selected['candidate_id']} "
        f"({robust_selected['design_class']}); its configured upper-quantile Lmax and "
        f"Smax were {_format_number(robust_selected['quantile_l_max_kg_per_m'])} and "
        f"{_format_number(robust_selected['quantile_s_max_kg_per_m'])} kg m-1. "
        f"Table 8 compares this result with {len(nominal_knees)} nominal knees and the "
        "remaining candidate set."
    )
    document.add_paragraph(
        "Manufacturable segment mapping, generic surface mapping, and slope rounding "
        "changed the primary outcomes by the amounts reported in Table 3. "
        "Frontier-wide complexity and "
        "manufacturing-screen metrics are reported in Table 6; Table 7 reports choices "
        "under no, base, and high transition penalties. Labor-scarcity scenarios weight "
        "manual intervention directly (Table 5) and were not assigned to actual "
        "communities. Table 4 varies snowfall severity, shedding penalties, allowable "
        "release, and labor scarcity. Strategy classifications are model-derived labels "
        "rather than building-code recommendations."
    )
    jma_path = results / "jma_daily_evaluation.csv"
    if jma_path.exists():
        jma = pd.read_csv(jma_path)
        document.add_heading("3.4 JMA station-winter scenarios", level=2)
        document.add_paragraph(
            f"Daily forcing covered {jma['station_id'].nunique()} stations and "
            f"{jma[['station_id', 'winter']].drop_duplicates().shape[0]} "
            "station-winters. Table 9 reports the selected uniform and joint profiles "
            "under these observations. Daily aggregation coarsens event timing, "
            "so these outputs are supplementary scenario checks and not comparable to "
            "hourly shedding observations."
        )

    document.add_heading("4. Discussion", level=1)
    document.add_paragraph(
        "The analysis demonstrates how spatial grading can be evaluated against a fully "
        "optimized uniform reference rather than a single hand-picked roof. The computed "
        "fronts support only conditional statements within the reduced-order model. A "
        "larger normalized hypervolume or a favorable selected knee does not imply that "
        "every heterogeneous design is better, nor that the same relation persists under "
        "unmodeled wind, geometry, or material behavior."
    )
    document.add_paragraph(
        "The main design implication is methodological: passive snow-management concepts "
        "should be compared as trade-off sets, with manufacturability and operational "
        "preferences included explicitly. The generic surface mapping shows how a smooth "
        "continuous optimum can be translated into a small material-class vocabulary "
        "while measuring the resulting objective loss."
    )
    document.add_heading("4.1 Limitations", level=2)
    document.add_paragraph(
        "The model has not been calibrated or validated against roof-scale shedding "
        "measurements. It omits wind redistribution, three-dimensional flow, snow "
        "fracture and slab mechanics, cornices, local roof details, heat transfer through "
        "the assembly, impact trajectories, drainage blockage, structural response, and "
        "pedestrian exposure. Friction, adhesion, compaction, melt, and aging parameters "
        "include explicit assumptions. Daily JMA observations do not resolve subdaily "
        "events, and ground snowfall or snow depth is not roof snow mass. Accordingly, "
        "the study does not establish structural safety, pedestrian safety, code "
        "compliance, injury reduction, lifecycle cost, or universal effectiveness."
    )
    document.add_heading("4.2 Future validation", level=2)
    document.add_paragraph(
        "Future work should calibrate interface parameters across temperature, liquid-"
        "water content, roughness, aging, and load; validate mass and release timing "
        "against instrumented roofs; add wind redistribution and three-dimensional edge "
        "effects; and predefine external-validation metrics before fitting."
    )

    document.add_heading("5. Conclusions", level=1)
    document.add_paragraph(
        "A reproducible reduced-order workflow compared complete optimized uniform and "
        "spatially heterogeneous passive roof-snow trade-off sets. The results quantify "
        "how grading changes modeled retained-mass and discrete-release objectives under "
        "synthetic and supplementary JMA forcing, with explicit convergence, ablation, "
        "sensitivity, robustness, and complexity analyses. The outputs are hypotheses "
        "and design-space evidence for future roof-scale validation, not design approval "
        "or safety certification."
    )

    document.add_heading("Declarations", level=1)
    document.add_paragraph(f"Funding: {metadata['funding']}")
    document.add_paragraph(
        f"Declaration of competing interests: {metadata['competing_interests']}"
    )
    document.add_paragraph(
        "Data and code availability: Source code, immutable public-data snapshots, "
        "acquisition metadata, generated result tables, and reproduction instructions "
        "are available at https://github.com/bougtoir/"
        "functionally-graded-roof-snow-management."
    )
    document.add_paragraph(
        "Generative AI statement: During preparation, the author used Devin "
        "(Cognition AI) to support coding, public-data acquisition, analysis scripting, "
        "and drafting. The author must review and edit the final submission and remains "
        "responsible for its content."
    )
    document.add_paragraph(
        "CRediT authorship contribution statement: REQUIRED—author confirmation of "
        "roles before submission."
    )

    document.add_heading("References", level=1)
    for index, row in references.iterrows():
        document.add_paragraph(f"{index + 1}. {_reference_text(row)}")

    document.add_page_break()
    document.add_heading("Editable tables", level=1)
    _add_dataframe_table(
        document,
        table_1,
        "Table 1. Pareto-front summary.",
        [
            "design_class",
            "pareto_designs",
            "knee_l_max_kg_per_m",
            "knee_s_max_kg_per_m",
            "normalized_hypervolume",
            "additive_epsilon_vs_uniform",
            "dominated_fraction_in_combined_set",
        ],
        headers=[
            "Class",
            "Pareto n",
            "Knee Lmax",
            "Knee Smax",
            "Norm. HV",
            "Epsilon vs uniform",
            "Dominated fraction",
        ],
    )
    _add_dataframe_table(
        document,
        table_2,
        "Table 2. Selected joint-profile cell properties.",
        [
            "cell",
            "continuous_slope_deg",
            "discrete_slope_deg",
            "continuous_mu_static",
            "continuous_adhesion_pa",
            "discrete_material_class",
        ],
        headers=[
            "Cell",
            "Continuous slope",
            "Discrete slope",
            "Continuous friction",
            "Continuous adhesion",
            "Generic class",
        ],
    )
    _add_dataframe_table(
        document,
        table_3.assign(
            mapping=table_3["mapping"].replace(
                {"manufacturable_discrete_generic_classes": "discrete_generic"}
            )
        ),
        "Table 3. Continuous-to-discrete profile loss.",
        [
            "mapping",
            "l_max_kg_per_m",
            "s_max_kg_per_m",
            "mean_ssci",
            "mean_event_count",
            "slope_transition_count",
            "surface_transition_count",
            "l_max_discretization_loss",
            "s_max_discretization_loss",
        ],
        headers=[
            "Mapping",
            "Lmax",
            "Smax",
            "Mean SSCI",
            "Event count",
            "Slope transitions",
            "Surface transitions",
            "Lmax loss",
            "Smax loss",
        ],
    )
    document.add_paragraph(
        "Table 4 (strategy phase-diagram classifications) is supplied separately as "
        "an editable CSV because the complete table is too large for useful display "
        "in the manuscript."
    )
    _add_dataframe_table(
        document,
        table_5,
        "Table 5. Frozen labor-scarcity decision choices.",
        [
            "labor_scarcity",
            "selected_design_class",
            "strategy",
            "l_max_kg_per_m",
            "s_max_kg_per_m",
            "mean_manual_triggers",
        ],
        headers=[
            "Labor scarcity",
            "Design class",
            "Strategy",
            "Lmax",
            "Smax",
            "Manual triggers",
        ],
    )
    _add_dataframe_table(
        document,
        pd.concat(
            [
                group.iloc[sorted({0, len(group) // 2, len(group) - 1})]
                for _, group in table_6.groupby("design_class", sort=False)
            ],
            ignore_index=True,
        ),
        "Table 6. Complexity metrics for selected frontier rows.",
        [
            "design_class",
            "l_max_kg_per_m",
            "s_max_kg_per_m",
            "maximum_adjacent_slope_change_deg",
            "transition_count",
            "minimum_segment_cells",
            "meets_minimum_segment_length",
            "meets_maximum_transitions",
        ],
        headers=[
            "Class",
            "Lmax",
            "Smax",
            "Max slope change",
            "Transitions",
            "Min segment cells",
            "Min segment met",
            "Transition limit met",
        ],
    )
    _add_dataframe_table(
        document,
        table_7,
        "Table 7. Complexity-penalty selections.",
        [
            "transition_penalty",
            "design_class",
            "l_max_kg_per_m",
            "s_max_kg_per_m",
            "transition_count",
            "selection_score",
        ],
        headers=[
            "Penalty",
            "Class",
            "Lmax",
            "Smax",
            "Transitions",
            "Score",
        ],
    )
    _add_dataframe_table(
        document,
        table_8,
        "Table 8. Monte Carlo robustness summary for candidate designs.",
        [
            "candidate_id",
            "design_class",
            "nominal_l_max_kg_per_m",
            "nominal_s_max_kg_per_m",
            "quantile_l_max_kg_per_m",
            "quantile_s_max_kg_per_m",
            "probability_manual_intervention",
            "robust_selected",
        ],
        maximum_rows=30,
        headers=[
            "Candidate",
            "Class",
            "Nominal Lmax",
            "Nominal Smax",
            "Q95 Lmax",
            "Q95 Smax",
            "P(manual)",
            "Robust selected",
        ],
    )
    if jma_path.exists():
        table_9 = pd.read_csv(tables / "table_9_jma_daily_evaluation.csv")
        _add_dataframe_table(
            document,
            table_9,
            "Table 9. Supplementary JMA daily station-winter evaluation.",
            [
                "station_id",
                "winter",
                "days",
                "design_class",
                "l_max_kg_per_m",
                "s_max_kg_per_m",
                "mean_event_count",
                "mean_ssci",
            ],
            headers=[
                "Station",
                "Winter",
                "Days",
                "Design",
                "Lmax",
                "Smax",
                "Events",
                "Mean SSCI",
            ],
        )
    document.add_heading("Figure captions", level=1)
    for caption in FIGURE_CAPTIONS:
        document.add_paragraph(caption)

    _enforce_ascii(document)
    output = root / "manuscript" / "build" / "manuscript.docx"
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    submission_output = root / "manuscript" / "manuscript_CRST.docx"
    document.save(submission_output)
    return submission_output


def _find_paragraph(document: Document, text: str):
    for paragraph in document.paragraphs:
        if text in paragraph.text:
            return paragraph
    raise ValueError(f"paragraph not found: {text}")


def _remove_paragraph(paragraph) -> None:
    parent = paragraph._p.getparent()
    if parent is not None:
        parent.remove(paragraph._p)


def _insert_after(paragraph, elements: list) -> None:
    anchor = paragraph._p
    for element in elements:
        anchor.addnext(element)
        anchor = element


def _figure_elements(document: Document, path: Path, caption: str) -> list:
    image_paragraph = document.add_paragraph()
    image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    image_paragraph.paragraph_format.space_before = Pt(12)
    image_paragraph.add_run().add_picture(str(path), width=Inches(6.2))
    caption_paragraph = document.add_paragraph(caption, style="Caption")
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.space_before = Pt(12)
    caption_paragraph.paragraph_format.space_after = Pt(6)
    return [image_paragraph._p, caption_paragraph._p]


def build_inline_manuscript(root: Path) -> Path:
    source = root / "manuscript" / "manuscript_CRST.docx"
    document = Document(source)

    table_4 = pd.read_csv(
        root / "tables" / "generated" / "table_4_strategy_phase_diagram.csv"
    )
    _add_dataframe_table(
        document,
        table_4,
        "Table 4. Strategy phase-diagram classifications "
        "(selected columns; the complete table is supplied as CSV).",
        [
            "snowfall_factor",
            "shedding_penalty_weight",
            "labor_scarcity",
            "allowable_shed_kg_per_m",
            "constraint_feasible",
            "selected_design_class",
            "strategy",
            "mean_manual_triggers",
        ],
        headers=[
            "Snowfall factor",
            "Shed penalty",
            "Labor scarcity",
            "Allowable shed",
            "Feasible",
            "Class",
            "Strategy",
            "Manual triggers",
        ],
    )

    table_elements = {}
    for number in range(1, 10):
        caption = next(
            paragraph
            for paragraph in document.paragraphs
            if paragraph.text.startswith(f"Table {number}.")
        )
        table = caption._p.getnext()
        if table is None or table.tag != qn("w:tbl"):
            raise ValueError(f"editable table missing after Table {number} caption")
        caption.paragraph_format.space_before = Pt(12)
        caption.paragraph_format.space_after = Pt(6)
        table_elements[number] = [caption._p, table]

    editable_heading = _find_paragraph(document, "Editable tables")
    preceding = editable_heading._p.getprevious()
    if preceding is not None:
        page_breaks = preceding.findall(f".//{qn('w:br')}")
        if any(item.get(qn("w:type")) == "page" for item in page_breaks):
            preceding.getparent().remove(preceding)
    _remove_paragraph(editable_heading)
    _remove_paragraph(_find_paragraph(document, "Table 4 (strategy phase-diagram"))
    _remove_paragraph(_find_paragraph(document, "Figure captions"))
    for caption in FIGURE_CAPTIONS:
        _remove_paragraph(_find_paragraph(document, caption))

    primary_anchor = _find_paragraph(document, "Figure 1 summarizes")
    convergence_anchor = _find_paragraph(document, "Figure 6 reports")
    robustness_anchor = _find_paragraph(document, "Figures 8-9 and Tables 4-8")
    jma_anchor = _find_paragraph(document, "Table 9 reports")

    figure_elements = {
        number: _figure_elements(
            document,
            root / "figures" / "png" / filename,
            FIGURE_CAPTIONS[number - 1],
        )
        for number, filename in enumerate(FIGURE_FILENAMES, start=1)
    }
    _insert_after(
        primary_anchor,
        [
            *figure_elements[1],
            *figure_elements[2],
            *figure_elements[3],
            *figure_elements[4],
            *figure_elements[5],
            *table_elements[1],
            *table_elements[2],
            *table_elements[3],
        ],
    )
    _insert_after(
        convergence_anchor,
        [*figure_elements[6], *figure_elements[7]],
    )
    _insert_after(
        robustness_anchor,
        [
            *figure_elements[8],
            *figure_elements[9],
            *table_elements[4],
            *table_elements[5],
            *table_elements[6],
            *table_elements[7],
            *table_elements[8],
        ],
    )
    _insert_after(jma_anchor, table_elements[9])

    _enforce_ascii(document)
    output = root / "manuscript" / "manuscript_CRST_inline.docx"
    document.save(output)
    return output


def build_editable_tables(root: Path) -> Path:
    source = Document(root / "manuscript" / "manuscript_CRST_inline.docx")
    document = Document()
    _configure_document(document)
    document.add_heading("Editable manuscript tables", level=0)
    document.add_paragraph(TITLE)
    body = document._body._element
    for number in range(1, 10):
        caption = next(
            paragraph
            for paragraph in source.paragraphs
            if paragraph.text.startswith(f"Table {number}.")
        )
        table = caption._p.getnext()
        if table is None or table.tag != qn("w:tbl"):
            raise ValueError(f"editable table missing after Table {number} caption")
        body.insert(len(body) - 1, deepcopy(caption._p))
        body.insert(len(body) - 1, deepcopy(table))
    _enforce_ascii(document)
    output = root / "manuscript" / "editable_tables_CRST.docx"
    document.save(output)
    return output


def build_editable_figures(root: Path) -> Path:
    presentation = Presentation()
    presentation.slide_width = PptxInches(13.333)
    presentation.slide_height = PptxInches(7.5)
    blank_layout = presentation.slide_layouts[6]

    for number, (filename, caption) in enumerate(
        zip(FIGURE_FILENAMES, FIGURE_CAPTIONS, strict=True),
        start=1,
    ):
        slide = presentation.slides.add_slide(blank_layout)
        title = slide.shapes.add_textbox(
            PptxInches(0.5),
            PptxInches(0.15),
            PptxInches(12.333),
            PptxInches(0.5),
        )
        title_frame = title.text_frame
        title_frame.clear()
        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.text = f"Figure {number}"
        title_paragraph.alignment = PP_ALIGN.CENTER
        title_paragraph.runs[0].font.name = "Arial"
        title_paragraph.runs[0].font.size = PptxPt(24)
        title_paragraph.runs[0].font.bold = True

        image_path = root / "figures" / "png" / filename
        with Image.open(image_path) as image:
            image_width, image_height = image.size
        width = 12.0
        height = width * image_height / image_width
        if height > 5.6:
            height = 5.6
            width = height * image_width / image_height
        slide.shapes.add_picture(
            str(image_path),
            PptxInches((13.333 - width) / 2),
            PptxInches(0.85 + (5.6 - height) / 2),
            width=PptxInches(width),
            height=PptxInches(height),
        )

        caption_box = slide.shapes.add_textbox(
            PptxInches(0.5),
            PptxInches(6.55),
            PptxInches(12.333),
            PptxInches(0.65),
        )
        caption_frame = caption_box.text_frame
        caption_frame.clear()
        caption_paragraph = caption_frame.paragraphs[0]
        caption_paragraph.text = caption
        caption_paragraph.alignment = PP_ALIGN.CENTER
        caption_paragraph.runs[0].font.name = "Arial"
        caption_paragraph.runs[0].font.size = PptxPt(11)

    output = root / "manuscript" / "editable_figures_CRST.pptx"
    presentation.save(output)
    return output


def build_supplement(root: Path) -> Path:
    document = Document()
    _configure_document(document)
    document.add_heading("Supplementary material", level=0)
    document.add_paragraph(TITLE)
    document.add_heading("S1. Frozen analysis and implementation", level=1)
    document.add_paragraph(
        "The analysis plan, machine-readable freeze, and deviation log are included "
        "in the repository. All primary outcomes, optimization seeds, resolution "
        "choices, and classification weights were defined before production results."
    )
    document.add_heading("S2. Reproduction", level=1)
    document.add_paragraph(
        "Create the pinned Python 3.11 environment, then run `make all`. The workflow "
        "validates source style and tests, regenerates processed synthetic and JMA "
        "weather, evaluates baselines and convergence, resumes or executes optimization, "
        "runs sensitivity and robustness, creates figures and editable tables, builds "
        "submission documents, validates them, and packages the submission."
    )
    document.add_heading("S3. Model scope", level=1)
    document.add_paragraph(
        "Cell mass balance is snowfall input minus melt and eave release. Static "
        "friction and adhesion define onset; kinetic friction defines transport. "
        "The model is deterministic for a fixed design and weather series. It is a "
        "threshold-release model rather than a structural, fracture-mechanics, or "
        "computational-fluid-dynamics model."
    )
    document.add_heading("S4. Public-data provenance", level=1)
    ledger = pd.read_csv(root / "data" / "metadata" / "acquisition_ledger.csv")
    counts = ledger["local_status"].value_counts().to_dict()
    document.add_paragraph(
        "The consolidated ledger contains "
        f"{len(ledger)} records: "
        + ", ".join(f"{key}={value}" for key, value in counts.items())
        + ". Each locally retained record includes a path, size, checksum, retrieval "
        "time, request context where applicable, and usage-conditions reference. "
        "Records marked not_recovered are historical child-worker scratch captures, "
        "not quantitative inputs. Quantitative inputs and redistributable evidence are "
        "retained in verified repository snapshots; non-redistributed third-party "
        "documents remain identified by provenance metadata."
    )
    document.add_heading("S5. Machine-readable outputs", level=1)
    document.add_paragraph(
        "Complete design-space, Pareto, per-seed history, sensitivity, robustness, "
        "JMA scenario, phase-diagram, and material-mapping tables are supplied as CSV. "
        "The selected manuscript values are generated directly from these files."
    )
    _enforce_ascii(document)
    output = root / "manuscript" / "build" / "supplement.docx"
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    submission_output = root / "manuscript" / "supplement_CRST.docx"
    document.save(submission_output)
    return submission_output


def build_cover_letter(root: Path) -> Path:
    metadata = yaml.safe_load(
        (root / "manuscript" / "author_metadata.yaml").read_text(encoding="utf-8")
    )
    author = next(item for item in metadata["authors"] if item.get("corresponding"))
    document = Document()
    _configure_document(document)
    document.add_paragraph("Editor-in-Chief")
    document.add_paragraph("Cold Regions Science and Technology")
    document.add_paragraph("Dear Editor,")
    document.add_paragraph(
        f"Please consider our manuscript, “{TITLE},” as a Research Article in "
        "Cold Regions Science and Technology."
    )
    document.add_paragraph(
        "The manuscript presents a reproducible reduced-order comparison of optimized "
        "spatially uniform and functionally graded passive roof-snow strategies. It "
        "maps the complete retained-mass versus discrete-release trade-off, includes "
        "geometry and surface ablations, convergence, sensitivity, Monte Carlo "
        "perturbation, manufacturing-complexity analysis, and supplementary scenarios "
        "from official Japanese weather observations."
    )
    document.add_paragraph(
        "The work fits the journal because it addresses cold-regions roof-snow "
        "processes, explicitly positions the model against roof-snow literature, and "
        "states the need for empirical validation. It makes no claim of structural "
        "safety, code compliance, pedestrian safety, or universal performance."
    )
    document.add_paragraph(
        "REQUIRED before submission: corresponding-author confirmation that the "
        "manuscript is original, is not under consideration elsewhere, and has been "
        "approved by all authors."
    )
    document.add_paragraph(
        "All source code, public-data snapshots, checksum ledgers, and generated "
        "analysis artifacts are supplied in a public reproducibility repository."
    )
    document.add_paragraph("Sincerely,")
    document.add_paragraph(author["name"])
    document.add_paragraph(author["affiliation"])
    document.add_paragraph(author["postal_address"])
    document.add_paragraph(author["email"])
    _enforce_ascii(document)
    output = root / "manuscript" / "build" / "cover_letter.docx"
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    submission_output = root / "manuscript" / "cover_letter_CRST.docx"
    document.save(submission_output)
    return submission_output


def build_text_files(root: Path) -> list[Path]:
    build = root / "manuscript" / "build"
    build.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {
        "highlights.txt": (
            "- Uniform and graded roof-snow trade-off sets were optimized.\n"
            "- Spatial slope, friction, and adhesion profiles were compared.\n"
            "- Convergence, ablation, sensitivity, and robustness were quantified.\n"
            "- Outputs are reduced-order model evidence, not safety certification.\n"
        ),
        "scope_fit.md": (
            "# Scope fit\n\n"
            "The study addresses roof-snow accumulation and passive release in cold "
            "regions using reproducible computational modeling, official weather "
            "observations, and explicit links to roof-snow deposition, interface, and "
            "validation literature published in *Cold Regions Science and Technology*. "
            "The submission is framed as reduced-order design-space analysis and does "
            "not claim structural validation.\n"
        ),
        "crst_checklist.md": (
            "# CRST submission checklist\n\n"
            "- [x] Editable single-column Word manuscript\n"
            "- [x] Abstract no longer than 250 words\n"
            "- [x] Six keywords\n"
            "- [x] Separate highlights file with 3-5 bullets, each <=85 characters\n"
            "- [x] Continuous line numbering requested in DOCX XML\n"
            "- [x] Editable manuscript tables\n"
            "- [x] Figures supplied separately as EPS, PDF, SVG, TIFF, and PNG\n"
            "- [x] Data/code availability and generative-AI statements\n"
            "- [ ] Author affiliation and postal address confirmed\n"
            "- [ ] Funding and competing-interest declarations confirmed\n"
            "- [ ] CRediT roles confirmed by the author\n"
            "- [ ] Originality and author-approval statement confirmed\n"
            "- [ ] Current Guide for Authors manually rechecked before submission "
            "(archival acquisition returned HTTP 403)\n"
        ),
    }
    outputs = []
    for name, content in files.items():
        path = build / name
        path.write_text(content, encoding="utf-8")
        outputs.append(path)
    aliases = {
        "highlights.txt": "highlights_CRST.txt",
        "scope_fit.md": "CRST_scope_fit.md",
        "crst_checklist.md": "CRST_submission_checklist.md",
    }
    for source_name, alias_name in aliases.items():
        path = root / "manuscript" / alias_name
        path.write_text(files[source_name], encoding="utf-8")
        outputs.append(path)
    return outputs


def package_submission(root: Path) -> Path:
    output = root / "submission" / "CRST_submission_package.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    submission_files = [
        root / "manuscript" / "manuscript_CRST.docx",
        root / "manuscript" / "cover_letter_CRST.docx",
        root / "manuscript" / "supplement_CRST.docx",
        root / "manuscript" / "highlights_CRST.txt",
        root / "manuscript" / "CRST_submission_checklist.md",
        root / "manuscript" / "CRST_scope_fit.md",
    ]
    include_roots = [
        root / "figures" / "png",
        root / "figures" / "tiff",
        root / "figures" / "vector",
        root / "tables" / "generated",
    ]
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in submission_files:
            archive.write(path, path.name)
        for include_root in include_roots:
            for path in sorted(include_root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root))
    return output


def write_manifest(root: Path, paths: list[Path]) -> Path:
    manifest = []
    for path in paths:
        manifest.append(
            {
                "path": str(path.relative_to(root)),
                "size_bytes": path.stat().st_size,
            }
        )
    output = root / "manuscript" / "build" / "artifact_manifest.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output


def write_csv_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
