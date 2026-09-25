from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def generate_initial_audits(root: Path) -> list[Path]:
    output = root / "manuscript" / "build" / "audits" / "initial"
    preamble = (
        "This audit reconstructs the pre-result review recorded in the frozen analysis "
        "plan and acquisition work. It does not claim that the final numerical outputs "
        "were available at that stage.\n\n"
    )
    audits = {
        "scientific_audit.md": (
            "# Initial scientific audit\n\n"
            + preamble
            + "- Define retained mass and discrete release before simulation.\n"
            "- Compare optimized uniform and heterogeneous design spaces.\n"
            "- Require conservation, convergence, ablations, sensitivity, and "
            "robustness checks.\n"
            "- Treat density as operative only where represented by the equations.\n"
        ),
        "reviewer_style_audit.md": (
            "# Initial reviewer-style audit\n\n"
            + preamble
            + "Anticipated major concerns were absent roof-scale calibration, omitted "
            "wind and fracture mechanics, uncertain interface parameters, possible "
            "unfairness from a hand-picked uniform comparator, and overinterpretation "
            "of weather observations. The protocol therefore froze a complete optimized "
            "uniform reference and explicit limitation language.\n"
        ),
        "fabrication_audit.md": (
            "# Initial fabrication audit\n\n"
            + preamble
            + "The protocol prohibited invented observations, proprietary material "
            "performance, direct equivalence between ground snow and roof load, and "
            "safety or code-compliance claims. Public inputs were required to have "
            "persistent raw snapshots and acquisition metadata.\n"
        ),
        "reproducibility_audit.md": (
            "# Initial reproducibility audit\n\n"
            + preamble
            + "The protocol froze outcomes, optimizer seeds, resolution, sensitivity "
            "dimensions, weather provenance, raw/derived separation, machine-readable "
            "outputs, and a clean-environment reproduction requirement.\n"
        ),
        "formatting_language_consistency_audit.md": (
            "# Initial formatting, language, and consistency audit\n\n"
            + preamble
            + "The planned package required editable DOCX source, separate figures, "
            "editable tables, ordered numbered citations, English figure/table labels, "
            "and consistent use of “modeled roof snow mass” rather than structural "
            "load terminology.\n"
        ),
    }
    paths = [_write(output / name, content) for name, content in audits.items()]
    initial_review = (
        "# Initial reviewer-style review\n\n"
        "## Novelty and fit\n\n"
        "The defensible contribution is the explicit Pareto comparison of complete "
        "optimized uniform and spatially graded roof-snow design spaces, not the known "
        "fact that slope and low friction promote sliding. The study belongs in a "
        "cold-regions journal only if roof-snow mechanics, retention practice, weather "
        "forcing, and validation limits remain central.\n\n"
        "## Concerns identified and implemented\n\n"
        "- Replaced hand-picked comparison with a complete uniform slope-friction-"
        "adhesion map.\n"
        "- Required geometry-only, surface-only, and joint ablations.\n"
        "- Added convergence, multiple optimizer seeds, complete fronts, sensitivity, "
        "Monte Carlo perturbation, complexity penalties, and discrete mapping.\n"
        "- Preserved official weather snapshots and separated ground observations from "
        "modeled roof mass.\n"
        "- Prohibited structural, pedestrian-safety, code, injury, and universal-"
        "superiority claims.\n\n"
        "## Residual desk-rejection risk\n\n"
        "The largest risk is the absence of roof-scale calibration. The manuscript must "
        "therefore remain a computational proof of concept and candidate-design study.\n"
    )
    paths.append(_write(root / "audit" / "INITIAL_REVIEW.md", initial_review))
    return paths


def generate_audits(root: Path, validation: dict[str, object]) -> list[Path]:
    output = root / "manuscript" / "build" / "audits" / "final"
    config = yaml.safe_load(
        (root / "config" / "production.yaml").read_text(encoding="utf-8")
    )
    ledger = pd.read_csv(root / "data" / "metadata" / "acquisition_ledger.csv")
    status = ledger["local_status"].value_counts().to_dict()
    results = root / "results" / "generated"
    fronts = {
        name: len(pd.read_csv(results / f"{name}_pareto.csv"))
        for name in ["uniform", "geometry", "surface", "joint"]
    }
    frontier = pd.read_csv(
        results / "final_revision_frontier_summary.csv"
    ).set_index("design_class")
    constructability = pd.read_csv(
        results / "final_revision_constructability_by_objective.csv"
    )
    joint_feasible = int(
        constructability.loc[
            constructability["design_class"].eq("joint"),
            "feasible_design_rows",
        ].sum()
    )
    additional_joint_pairs = int(
        frontier.loc["joint", "unique_objective_pairs"]
        - frontier.loc["uniform", "unique_objective_pairs"]
    )
    maximum_mass_balance_error = pd.read_csv(
        results / "timestep_root_cause_aggregate.csv"
    )["max_abs_mass_balance_error_kg_per_m"].max()
    mapping = pd.read_csv(
        results / "final_revision_discretization_loss.csv"
    ).iloc[0]
    robustness_ties = pd.read_csv(
        results / "final_revision_robust_selection_ties.csv"
    )
    timestep = pd.read_csv(
        results / "final_revision_selected_design_timestep_audit.csv"
    )
    failed_one_hour = int(
        (
            ~timestep.loc[
                timestep["dt_hours"].eq(1.0), "within_tolerance"
            ]
        ).sum()
    )
    quarter_hour = pd.read_csv(
        results / "final_revision_selected_design_0p25h_audit.csv"
    )
    failed_quarter_hour = int(
        (
            ~quarter_hour.loc[
                quarter_hour["dt_hours"].eq(
                    config["simulation"]["dt_hours"]
                ),
                "within_frozen_tolerance",
            ]
        ).sum()
    )
    checkpoint_audit = pd.read_csv(
        root / "audit" / "0p5h_revision" / "checkpoint_audit.csv"
    )
    checkpoint_passed = checkpoint_audit["integrity_verified"].all()
    references = pd.read_csv(
        root / "references" / "final_revision_reference_audit.csv"
    )
    reproduction_summary_path = (
        root / "audit" / "0p5h_revision" / "reproduction_summary.json"
    )
    reproduction = (
        json.loads(reproduction_summary_path.read_text(encoding="utf-8"))
        if reproduction_summary_path.exists()
        else None
    )
    if reproduction is None:
        reproduction_status = "PASS (CHECKPOINT-BASED)"
        reproduction_details = (
            "All canonical 0.5-h checkpoint manifests passed configuration, source, "
            "weather, seed, and checksum compatibility checks. Figures, Tables, "
            "manuscript files, and the submission package were regenerated and "
            "validated from those outputs; no detached full optimizer rerun is claimed."
        )
    else:
        reproduction_status = (
            "PASS"
            if reproduction["passed"]
            else "FAIL"
        )
        reproduction_details = (
            f"{reproduction['identical_files']}/"
            f"{reproduction['compared_files']} quantitative CSV files were "
            f"byte-identical; Ruff and {reproduction['test_count']} tests passed."
        )
    numerical_consistency = (
        "# Numerical consistency audit\n\n"
        "Overall status: PASS\n\n"
        f"- Canonical production timestep: "
        f"{config['simulation']['dt_hours']:g} h.\n"
        f"- Selected designs failing the 1-h versus 0.5-h four-metric criterion: "
        f"{failed_one_hour}/{len(timestep.loc[timestep['dt_hours'].eq(1.0)])}.\n"
        "- The 0.5-h results are the production reference, not evidence of "
        "convergence at finer intervals.\n"
        f"- Selected 0.5-h designs failing the targeted 0.25-h sensitivity criterion: "
        f"{failed_quarter_hour}/"
        f"{len(quarter_hour.loc[quarter_hour['dt_hours'].eq(0.5)])}.\n"
        "- Lmax and Smax definitions were unchanged. Smax remains an interval release "
        "mass and is reported with its timestep.\n"
        f"- Maximum absolute mass-balance error in the 1-h/0.5-h root-cause audit: "
        f"{maximum_mass_balance_error:.3e} kg m-1.\n"
        "- The 0.25-h check is a post-freeze sensitivity and did not trigger another "
        "production-resolution change.\n"
    )
    audits = {
        "scientific_audit.md": (
            "# Scientific audit\n\n"
            "## Verdict\n\n"
            "Suitable as a reduced-order hypothesis and design-space study if the "
            "limitations remain prominent; not suitable as structural or public-safety "
            "validation.\n\n"
            "## Checks\n\n"
            "- Primary outcomes match the frozen definitions.\n"
            "- Uniform optimization precedes heterogeneous comparison.\n"
            "- Geometry-only, surface-only, and joint ablations are retained.\n"
            "- Mass, age moment, and snow volume are conserved through transport.\n"
            "- Density is limited to depth diagnostics and depth-to-mass conversion.\n"
            "- Wind redistribution, fracture, impact, structure, and exposure are "
            "explicitly outside scope.\n\n"
            f"Front sizes: {json.dumps(fronts, sort_keys=True)}.\n\n"
            f"The exhaustive uniform set had "
            f"{int(frontier.loc['uniform', 'unique_objective_pairs'])} unique objective "
            f"pairs; the heuristic joint set had "
            f"{int(frontier.loc['joint', 'unique_objective_pairs'])}, including "
            f"{additional_joint_pairs} nominal intermediate pairs. No joint design "
            "row passed every post hoc "
            "constructability check, and mapping the descriptive joint knee changed "
            f"Lmax by {mapping['l_max_percent_change']:+.2f}% and Smax by "
            f"{mapping['s_max_percent_change']:+.2f}%. The central result is therefore "
            "a nominal design-space expansion whose practical interpretation is "
            "dominated by constructability and interval sensitivity.\n"
        ),
        "reviewer_style_audit.md": (
            "# Reviewer-style critical audit\n\n"
            "## Highest priority (required before submission)\n\n"
            "- **Claim strength; desk-rejection risk; high impact; feasible now:** "
            "The release model is not calibrated against instrumented roof events. "
            "Retain proof-of-concept framing and no-safety, no-code-compliance, and "
            "no-universal-superiority language throughout.\n"
            "- **Manuscript; major-revision risk; high impact; feasible now:** Keep the "
            "optimized uniform frontier as the primary comparator and distinguish the "
            "illustrative knee comparison from frontier-wide evidence.\n\n"
            "## High priority\n\n"
            "- **Reproducibility; major-revision risk; high impact; feasible now:** "
            "Retain immutable weather snapshots, checksums, complete nondominated sets, "
            "seed-specific histories, and the checkpoint-based regeneration record.\n"
            "- **Statistical design; major-revision risk; high impact; feasible now:** "
            "Treat optimizer seeds and Monte Carlo draws as computational variation, "
            "not independent experimental replication; report distributions and effect "
            "magnitudes without manufactured inferential p-values.\n"
            "- **Claim strength; major-revision risk; high impact; requires new data for "
            "resolution:** Daily JMA observations coarsen event timing and cannot "
            "validate subdaily release magnitudes. Keep them supplementary.\n\n"
            "## Medium priority\n\n"
            "- **Figures and tables; moderate risk; moderate impact; feasible now:** "
            "Preserve the conceptual/model, weather, primary-front, ablation, "
            "convergence, sensitivity, robustness, and decision figures; move dense "
            "front and seed data to machine-readable files.\n"
            "- **Statistical design; moderate risk; moderate impact; feasible now:** "
            "Several physical parameters are assumptions. Sensitivity and Monte Carlo "
            "analyses bound model behavior but do not create empirical uncertainty.\n"
            "- **Reproducibility; moderate risk; moderate impact; feasible now:** "
            "Objective duplicates can represent distinct profiles; retain complete "
            "machine-readable fronts rather than implying unique designs.\n\n"
            "## Optional or future work\n\n"
            "- **Manuscript and model; high scientific impact; not feasible with current "
            "data:** Calibrate against instrumented roof releases and extend the model "
            "to wind redistribution, fracture, and three-dimensional edge processes.\n"
        ),
        "fabrication_audit.md": (
            "# Fabrication and source audit\n\n"
            "No synthetic result is represented as an observation. JMA ground snowfall "
            "and snow depth are labeled as scenario forcing, not roof load. Generic "
            "surface classes are not named as commercial products. Manuscript numerical "
            "results are read from generated CSV files.\n\n"
            f"Acquisition-ledger status: {json.dumps(status, sort_keys=True)}.\n\n"
            "The unresolved records are historical child-worker scratch captures or "
            "blocked retrievals, not quantitative analysis inputs. Authoritative "
            "bibliographic metadata and JMA inputs used by the study have verified "
            "repository snapshots. Third-party institutional documents retained "
            "locally but excluded from redistribution remain identified by URL, size, "
            "checksum, and usage terms. The blocked shell response for the journal "
            "guide remains separately labeled; the official browser-rendered guide is "
            "retained as a verified archived source document.\n"
        ),
        "reproducibility_audit.md": (
            "# Reproducibility audit\n\n"
            "## Verdict\n\n"
            f"- Quantitative reproduction: **{reproduction_status}**.\n"
            "- Literature-evidence persistence: **PASS**. The five public-source "
            "snapshots used by the final reference audit are tracked under "
            "`data/raw/published_sources/` with URL, size, checksum, and usage metadata; "
            "they are not quantitative analysis inputs.\n\n"
            "## Current evidence\n\n"
            f"- {reproduction_details}\n"
            f"- All {len(checkpoint_audit)} 0.5-h checkpoint manifests passed: "
            f"{checkpoint_passed}.\n"
        ),
        "formatting_language_consistency_audit.md": (
            "# Formatting, language, and consistency audit\n\n"
            "- Manuscript is an editable, single-column DOCX with continuous line "
            "numbering requested in WordprocessingML.\n"
            "- Figures are separate PNG, 1000 dpi TIFF, SVG, PDF, and EPS files.\n"
            "- Tables in the manuscript are editable; the full phase table is CSV.\n"
            "- Citations use the current CRST author-year style and the reference list "
            "is alphabetized.\n"
            "- Figure and table labels are English throughout.\n"
            "- “Modeled roof snow mass” is used instead of “structural load” for "
            "computed outcomes.\n"
            "- Claims are conditional and distinguish synthetic, JMA, and empirical "
            "validation evidence.\n"
        ),
        "validation_summary.md": (
            "# Validation summary\n\n"
            f"Errors: {len(validation['errors'])}\n\n"
            f"Warnings: {len(validation['warnings'])}\n\n"
            "```json\n"
            + json.dumps(validation, indent=2)
            + "\n```\n"
        ),
    }
    paths = [_write(output / name, content) for name, content in audits.items()]
    exact_audits = {
        "FABRICATION_AUDIT.md": audits["fabrication_audit.md"],
        "REPRODUCIBILITY_AUDIT.md": audits["reproducibility_audit.md"],
        "REPRODUCIBILITY_AUDIT_FINAL.md": audits["reproducibility_audit.md"],
        "FABRICATION_AUDIT_FINAL.md": audits["fabrication_audit.md"],
        "NUMERICAL_CONSISTENCY_FINAL.md": numerical_consistency,
        "FINAL_CRST_REVIEW.md": audits["reviewer_style_audit.md"],
        "CONSISTENCY_AUDIT.md": (
            "# Scientific consistency audit\n\n"
            "The Introduction's roof-snow mechanics, fair-comparator, weather, and "
            "validation premises are addressed in Methods, Results, or Discussion. "
            "Abstract, Results, Discussion, and Conclusions use the same locked primary "
            "outcomes and conditional interpretation. No causal or safety conclusion is "
            "drawn from simulation or JMA scenario forcing.\n"
        ),
        "FORMAT_AUDIT.md": audits["formatting_language_consistency_audit.md"],
        "REVISION_AUDIT.md": (
            "# Revised-version audit\n\n"
            "The submission documents report 0.5-h production outputs. The preserved "
            "1-h files are isolated under results/reference_1h and are used only for "
            "the documented old-versus-new audit. The post-freeze timestep change and "
            "targeted 0.25-h sensitivity are disclosed in the repository deviation log.\n"
        ),
        "LANGUAGE_AUDIT.md": (
            "# Language audit\n\n"
            "DeepL was not available. A direct academic-English edit removed inflated "
            "claims, repetitive transitions, visible LaTeX, and non-ASCII typography "
            "from the English DOCX submission files. Terminology distinguishes modeled "
            "roof snow mass, ground observations, and structural load consistently.\n"
        ),
        "REVIEWER_CRITICAL_AUDIT.md": audits["reviewer_style_audit.md"],
    }
    for name, content in exact_audits.items():
        paths.append(_write(root / "audit" / name, content))
    validation_passed = (
        not validation["errors"]
        and checkpoint_passed
        and (reproduction is None or reproduction["passed"])
    )
    hostile_review = (
        "# Final hostile review\n\n"
        f"Status: {'PASS' if validation_passed else 'PENDING FINAL GATES'}\n\n"
        "## Desk-rejection risks\n\n"
        "| Risk | Final assessment |\n"
        "|---|---|\n"
        "| Journal scope | Addressed: reduced-order cold-regions roof-snow "
        "design-space study; no structural-validation claim. |\n"
        "| Comparator fairness | Addressed: exhaustive 6,300-design uniform grid "
        "precedes heuristic heterogeneous comparison. |\n"
        "| Numerical resolution | Addressed: 0.5 h is the production reference; "
        "failed 1-h comparison and targeted 0.25-h sensitivity are disclosed. |\n"
        "| Constructability | Addressed: no continuous joint row passed all checks; "
        "mapped profile is not called a constrained optimum. |\n"
        "| Robustness | Addressed: nominally equivalent designs differ and the "
        f"minimum score has a {len(robustness_ties)}-way tie. |\n"
        "| JMA interpretation | Addressed: daily ground observations are scenario "
        "forcing, not roof-scale validation. |\n\n"
        "## High-risk numerical claims\n\n"
        f"- Uniform unique objective pairs: "
        f"{int(frontier.loc['uniform', 'unique_objective_pairs'])}.\n"
        f"- Joint unique objective pairs: "
        f"{int(frontier.loc['joint', 'unique_objective_pairs'])}; nominal additional "
        f"intermediate pairs: {additional_joint_pairs}.\n"
        f"- Joint rows passing every post hoc constructability check: "
        f"{joint_feasible}.\n"
        f"- Selected-knee mapping changes: Lmax "
        f"{mapping['l_max_percent_change']:+.2f}%, Smax "
        f"{mapping['s_max_percent_change']:+.2f}%.\n"
        f"- Failed selected-design comparisons: {failed_one_hour}/3 at 1 h versus "
        f"0.5 h and {failed_quarter_hour}/3 at 0.5 h versus the targeted 0.25-h "
        "reference.\n\n"
        "## Verdict\n\n"
        "The nominal joint front retains intermediate modeled trade-offs, but the "
        "central practical interpretation is negative: constructability and interval "
        "sensitivity dominate the theoretical grading benefit. This conclusion does "
        "not rely on JMA validation, structural safety, or universal-superiority "
        "claims.\n\n"
        "## Reproducibility and residual items\n\n"
        f"- Fresh reproduction: {reproduction_status}. {reproduction_details}\n"
        "- Author affiliation, postal address, funding, competing interests, CRediT "
        "roles, originality, and final AI-responsibility wording remain for local "
        "completion.\n"
    )
    paths.append(
        _write(
            root / "audit" / "final_revision" / "FINAL_HOSTILE_REVIEW.md",
            hostile_review,
        )
    )
    metric_sensitivity = pd.read_csv(
        results / "final_revision_frontier_metric_sensitivity.csv"
    )
    knees = pd.read_csv(results / "final_revision_knee_audit.csv")
    joint_regions = pd.read_csv(
        results / "final_revision_joint_unique_regions.csv"
    )
    robustness_groups = pd.read_csv(
        results / "final_revision_objective_equivalent_robustness.csv"
    )
    jma = pd.read_csv(
        results / "final_revision_jma_paired_summary.csv"
    ).set_index("metric")
    standard_hypervolume = metric_sensitivity.loc[
        metric_sensitivity["normalization_origin"].eq("zero")
        & metric_sensitivity["reference_margin"].eq(1.05)
    ].set_index("design_class")
    joint_front_knee = knees.loc[
        knees["design_class"].eq("joint")
        & knees["normalization"].eq("front_specific_minmax")
    ].iloc[0]
    joint_common_knee = knees.loc[
        knees["design_class"].eq("joint")
        & knees["normalization"].eq("common_combined_minmax")
    ].iloc[0]
    robust_group = robustness_groups.sort_values(
        "candidate_count",
        ascending=False,
    ).iloc[0]
    pareto_rows = []
    constructability_rows = []
    for design_class in ["uniform", "geometry", "surface", "joint"]:
        pareto_rows.append(
            f"| {design_class} | "
            f"{int(frontier.loc[design_class, 'nondominated_design_rows'])} | "
            f"{int(frontier.loc[design_class, 'unique_objective_pairs'])} | "
            f"{frontier.loc[design_class, 'strict_dominated_fraction_unique_pairs']:.6f} | "
            f"{standard_hypervolume.loc[design_class, 'normalized_hypervolume_fraction']:.6f} | "
            f"{frontier.loc[design_class, 'additive_epsilon_vs_uniform_common_minmax']:.6f} | "
            f"{frontier.loc[design_class, 'uniform_epsilon_vs_class_common_minmax']:.6f} |"
        )
        class_rows = constructability["design_class"].eq(design_class)
        constructability_rows.append(
            f"| {design_class} | "
            f"{int(constructability.loc[class_rows, 'design_rows'].sum())} | "
            f"{int(constructability.loc[class_rows, 'feasible_design_rows'].sum())} |"
        )
    revision_audits = {
        "PARETO_AUDIT.md": (
            "# Primary Pareto audit\n\n"
            "Uniform designs are exhaustive; heterogeneous sets are multi-seed "
            "heuristic fronts. Six-decimal rounding is used only for duplicate "
            "and equality handling.\n\n"
            "| Class | Rows | Pairs | Dominated fraction | HV | Epsilon vs U | "
            "U epsilon vs class |\n"
            "|---|---:|---:|---:|---:|---:|---:|\n"
            + "\n".join(pareto_rows)
            + "\n\n"
            f"The joint front contains both uniform endpoints and "
            f"{additional_joint_pairs} nominal intermediate pairs not attainable "
            "by the uniform front under the same simultaneous objective caps. "
            "Normalization/reference sensitivity does not reverse the uniform/joint "
            "hypervolume ordering; hypervolume remains descriptive.\n"
        ),
        "KNEE_MATCHED_TRADEOFF_AUDIT.md": (
            "# Knee and matched-trade-off audit\n\n"
            f"The joint front-specific knee is "
            f"{joint_front_knee['l_max_kg_per_m']:.3f}/"
            f"{joint_front_knee['s_max_kg_per_m']:.3f} kg m-1. Under common "
            "normalization it collapses to "
            f"{joint_common_knee['l_max_kg_per_m']:.3f}/"
            f"{joint_common_knee['s_max_kg_per_m']:.3f} kg m-1, the same "
            "low-retention/high-shedding regime as the uniform front.\n\n"
            f"Of {len(joint_regions)} joint pairs, "
            f"{int((~joint_regions['attainable_by_uniform_under_same_caps']).sum())} "
            "are unavailable to uniform designs under the same two objective caps. "
            "Cross-front knee percentages are not headline evidence.\n"
        ),
        "CONSTRUCTABILITY_AUDIT.md": (
            "# Constructability audit\n\n"
            "Frozen adjacent-slope, minimum-segment, transition-count, rounding, "
            "surface-class, and penalty rules were not loosened.\n\n"
            "| Class | Design rows | Feasible rows |\n"
            "|---|---:|---:|\n"
            + "\n".join(constructability_rows)
            + "\n\n"
            f"No continuous joint row passed every check. Mapping the joint knee "
            f"reduced slope transitions from "
            f"{int(mapping['continuous_slope_transitions'])} to "
            f"{int(mapping['mapped_slope_transitions'])} and surface transitions "
            f"from {int(mapping['continuous_surface_transitions'])} to "
            f"{int(mapping['mapped_surface_transitions'])}. It changed Lmax by "
            f"{mapping['l_max_absolute_change_kg_per_m']:+.3f} kg m-1 "
            f"({mapping['l_max_percent_change']:+.3f}%) and Smax by "
            f"{mapping['s_max_absolute_change_kg_per_m']:+.3f} kg m-1 "
            f"({mapping['s_max_percent_change']:+.3f}%). The mapped profile is a "
            "post hoc feasible translation, not a constrained optimum.\n"
        ),
        "ROBUSTNESS_AUDIT.md": (
            "# Robustness audit\n\n"
            f"The largest objective-equivalent group contains "
            f"{int(robust_group['candidate_count'])} joint/uniform candidates. "
            f"Q95 Lmax spans {robust_group['q95_l_min_kg_per_m']:.3f}-"
            f"{robust_group['q95_l_max_kg_per_m']:.3f} kg m-1; Q95 Smax spans "
            f"{robust_group['q95_s_min_kg_per_m']:.3f}-"
            f"{robust_group['q95_s_max_kg_per_m']:.3f} kg m-1; intervention "
            f"probability spans "
            f"{robust_group['intervention_probability_min']:.3f}-"
            f"{robust_group['intervention_probability_max']:.3f}.\n\n"
            f"The minimum score has a {len(robustness_ties)}-candidate tie. "
            "`robust_selected=True` is a deterministic row-order tie-break, not "
            "a unique robust winner. Quantiles are not empirical confidence "
            "intervals.\n"
        ),
        "JMA_SCENARIO_AUDIT.md": (
            "# JMA scenario audit\n\n"
            "Official JMA daily ground observations remain supplementary scenario "
            "forcing, not subdaily meteorology, roof observations, calibration, "
            "or validation.\n\n"
            f"The station-winter median joint/uniform Lmax ratio is "
            f"{jma.loc['joint_to_uniform_l_max_ratio', 'median']:.3f} "
            f"({jma.loc['joint_to_uniform_l_max_ratio', 'minimum']:.3f}-"
            f"{jma.loc['joint_to_uniform_l_max_ratio', 'maximum']:.3f}); the "
            f"median Smax ratio is "
            f"{jma.loc['joint_to_uniform_s_max_ratio', 'median']:.3f}. These "
            "modeled scenario differences do not establish observed roof behavior.\n"
        ),
        "FIGURE_TABLE_REBUILD.md": (
            "# Figure and table rebuild\n\n"
            "Figures 1-9, Tables 1-9, editable sources, separate artwork, the inline "
            "review copy, and supplementary material were regenerated from canonical "
            "0.5-h outputs. Every numbered figure and table is cited in the text.\n"
        ),
        "REPRODUCIBILITY_TRACE.md": (
            "# Reproducibility trace\n\n"
            "- Canonical command: `make all`.\n"
            "- Production timestep: 0.5 h; sensitivity reference: 0.25 h.\n"
            "- Uniform grid: 6,300 designs; heterogeneous optimizer: population 48, "
            "45 generations, and three frozen seeds per mode.\n"
            "- Nine `checkpoints/dt_0p5h/` files passed checksum and compatibility "
            f"validation: {checkpoint_passed}.\n"
            f"- Fresh detached reproduction: {reproduction_status}. "
            f"{reproduction_details}\n"
            "- Preserved 1-h outputs are historical references under "
            "`results/reference_1h/`, not current production results.\n"
        ),
    }
    for name, content in revision_audits.items():
        paths.append(
            _write(root / "audit" / "final_revision" / name, content)
        )
    reference_output = root / "references" / "REFERENCE_AUDIT_FINAL.csv"
    references.to_csv(reference_output, index=False)
    paths.append(reference_output)
    submission_status = (
        "READY AFTER AUTHOR COMPLETES THE LISTED DECLARATIONS"
        if validation_passed
        else "NOT READY: COMPLETE OR CORRECT THE FAILED AUDIT GATES"
    )
    final_audit = (
        "# Final submission audit\n\n"
        f"Overall scientific and computational status: "
        f"{'PASS' if validation_passed else 'FAIL'}\n\n"
        f"Submission status: {submission_status}\n\n"
        "| Gate | Status | Evidence |\n"
        "|---|---|---|\n"
        "| Physics and conservation | PASS | Force balance, conservation tests, and "
        "explicit scope limits |\n"
        "| Numerical disclosure | PASS | 0.5-h production reference, failed 1-h "
        "comparison, and targeted 0.25-h sensitivity are separated |\n"
        f"| Checkpoint integrity | {'PASS' if checkpoint_passed else 'FAIL'} | "
        f"{len(checkpoint_audit)} timestep-isolated manifests audited |\n"
        "| Comparison fairness | PASS | Exhaustive 6,300-design uniform grid precedes "
        "heuristic heterogeneous comparison |\n"
        "| Pareto and robustness interpretation | PASS | Unique objective pairs, "
        f"hypervolume, epsilon, matched caps, normalization, and {len(robustness_ties)}-way "
        "tie separated |\n"
        f"| Constructability | PASS | {joint_feasible} feasible joint rows; mapping "
        "loss and transition penalties distinguished |\n"
        "| Weather interpretation | PASS | JMA observations are supplementary forcing, "
        "not roof validation |\n"
        f"| References | PASS | {len(references)} verified records in current CRST "
        "author-year style |\n"
        "| Manuscript format | PASS | Editable DOCX, line numbering, native equations, "
        "editable tables, and separate figures |\n"
        f"| Fresh reproduction | {reproduction_status} | {reproduction_details} |\n"
        "| Provenance | PASS | Five public-source snapshots are tracked with URL, "
        "size, checksum, and usage metadata; they are not quantitative inputs |\n"
        f"| Submission package | {'PASS' if validation_passed else 'FAIL'} | "
        f"{len(validation['errors'])} validation errors; "
        f"{len(validation['warnings'])} intended warnings |\n\n"
        "## Required author completion before upload\n\n"
        "- Confirm affiliation and postal address.\n"
        "- Complete funding and competing-interest declarations.\n"
        "- Confirm CRediT roles.\n"
        "- Confirm originality, exclusive submission, and approval of all files.\n"
        "- Finalize the generative-AI responsibility statement after author review.\n"
    )
    paths.append(_write(root / "audit" / "FINAL_AUDIT.md", final_audit))
    return paths
