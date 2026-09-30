from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from graded_roof.complexity import manufacturable_mapping
from graded_roof.optimization import _checkpoint_metadata, _load_checkpoint
from graded_roof.simulation import simulate
from graded_roof.study import (
    evaluate_design,
    heterogeneous_design,
    result_record,
    simulation_config,
    synthetic_weather_set,
    uniform_design,
)
from graded_roof.weather import resample_weather

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "generated"
REFERENCE = ROOT / "results" / "reference_1h"
AUDIT = ROOT / "audit" / "0p5h_revision"
OBJECTIVES = ["l_max_kg_per_m", "s_max_kg_per_m"]
TIMESTEP_METRICS = [
    "l_max_kg_per_m",
    "s_max_kg_per_m",
    "mean_event_count",
    "mean_ssci",
    "mean_total_shed_kg_per_m",
    "mean_residual_mass_kg_per_m",
]


def _config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _select_knee(front: pd.DataFrame) -> pd.Series:
    objectives = front[OBJECTIVES].to_numpy(float)
    span = np.ptp(objectives, axis=0)
    normalized = (objectives - objectives.min(axis=0)) / np.where(
        span > 0,
        span,
        1.0,
    )
    return front.iloc[int(np.argmin(np.linalg.norm(normalized, axis=1)))]


def _front_design(row: pd.Series, config: dict, mode: str, label: str):
    columns = sorted(
        [column for column in row.index if column.startswith("x_")],
        key=lambda column: int(column.split("_", maxsplit=1)[1]),
    )
    return replace(
        heterogeneous_design(
            row[columns].to_numpy(float),
            config,
            mode,
            label=label,
        ),
        label=label,
    )


def _selected_designs(config: dict, directory: Path):
    uniform_row = _select_knee(pd.read_csv(directory / "uniform_pareto.csv"))
    joint_row = _select_knee(pd.read_csv(directory / "joint_pareto.csv"))
    uniform = uniform_design(
        config,
        float(uniform_row["slope_deg"]),
        float(uniform_row["mu_static"]),
        float(uniform_row["adhesion_pa"]),
        label="uniform_knee",
    )
    joint = _front_design(
        joint_row,
        config,
        "joint",
        "joint_continuous_knee",
    )
    mapped, _ = manufacturable_mapping(
        joint,
        config["surface"]["discrete_classes"],
        slope_rounding_deg=config["complexity"]["slope_rounding_deg"],
        minimum_segment_cells=config["roof"]["minimum_segment_cells"],
        maximum_transitions=config["roof"]["maximum_transitions"],
        maximum_adjacent_slope_change_deg=config["roof"][
            "adjacent_slope_limit_deg"
        ],
    )
    return [
        uniform,
        joint,
        replace(mapped, label="joint_mapped_knee"),
    ]


def _aggregate_at_steps(
    config: dict,
    designs: list,
    steps: list[float],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    master_config = json.loads(json.dumps(config))
    master_config["simulation"]["dt_hours"] = min(steps)
    master_weathers = synthetic_weather_set(master_config)
    settings = simulation_config(config)
    aggregate_rows = []
    scenario_rows = []
    for design in designs:
        for dt_hours in steps:
            weathers = [
                resample_weather(weather, dt_hours)
                for weather in master_weathers
            ]
            aggregate, _ = evaluate_design(design, weathers, settings)
            aggregate_rows.append(
                {
                    "design": design.label,
                    "dt_hours": dt_hours,
                    **{
                        key: value
                        for key, value in aggregate.items()
                        if key != "design"
                    },
                }
            )
            for source_weather, weather in zip(
                master_weathers,
                weathers,
                strict=True,
            ):
                scenario_rows.append(
                    {
                        "design": design.label,
                        "scenario": source_weather.name,
                        "dt_hours": dt_hours,
                        **result_record(simulate(design, weather, settings)),
                    }
                )
    return pd.DataFrame(aggregate_rows), pd.DataFrame(scenario_rows)


def _relative_change(new: float, old: float) -> float:
    return np.nan if np.isclose(old, 0.0) else (new - old) / abs(old)


def stage_timestep() -> None:
    config = _config(REFERENCE / "production_1h.yaml")
    designs = _selected_designs(config, REFERENCE)
    aggregate, scenarios = _aggregate_at_steps(
        config,
        designs,
        [1.0, 0.5],
    )
    comparison_rows = []
    for design, group in aggregate.groupby("design"):
        old = group.loc[group["dt_hours"].eq(1.0)].iloc[0]
        new = group.loc[group["dt_hours"].eq(0.5)].iloc[0]
        for metric in TIMESTEP_METRICS:
            comparison_rows.append(
                {
                    "design": design,
                    "metric": metric,
                    "value_1h": old[metric],
                    "value_0p5h": new[metric],
                    "absolute_change": new[metric] - old[metric],
                    "relative_change": _relative_change(
                        float(new[metric]),
                        float(old[metric]),
                    ),
                }
            )
    comparison = pd.DataFrame(comparison_rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    aggregate.to_csv(
        RESULTS / "timestep_root_cause_aggregate.csv",
        index=False,
    )
    scenarios.to_csv(
        RESULTS / "timestep_root_cause_scenarios.csv",
        index=False,
    )
    comparison.to_csv(
        RESULTS / "timestep_root_cause_comparison.csv",
        index=False,
    )

    scenario_pairs = scenarios.pivot(
        index=["design", "scenario"],
        columns="dt_hours",
        values=[
            "input_snow_kg_per_m",
            "total_shed_kg_per_m",
            "s_max_kg_per_m",
            "shed_event_count",
            "mass_balance_error_kg_per_m",
        ],
    )
    input_difference = (
        scenario_pairs["input_snow_kg_per_m"][0.5]
        - scenario_pairs["input_snow_kg_per_m"][1.0]
    ).abs().max()
    total_shed_relative = (
        (
            scenario_pairs["total_shed_kg_per_m"][0.5]
            - scenario_pairs["total_shed_kg_per_m"][1.0]
        ).abs()
        / scenario_pairs["total_shed_kg_per_m"][0.5].abs().clip(lower=1e-12)
    ).max()
    s_max_relative = comparison.loc[
        comparison["metric"].eq("s_max_kg_per_m"),
        "relative_change",
    ].abs().max()
    event_relative = comparison.loc[
        comparison["metric"].eq("mean_event_count"),
        "relative_change",
    ].abs().max()
    maximum_balance_error = scenarios[
        "mass_balance_error_kg_per_m"
    ].abs().max()
    mechanism = (
        "The identical forcing totals and substantially larger change in "
        "`S_max` than in total shed mass identify within-step aggregation and "
        "threshold-event partitioning as the main cause. Snowfall/melt timing "
        "and transport discretization contribute to the remaining retained-mass "
        "and SSCI differences."
        if s_max_relative > total_shed_relative
        else "The changes are not explained by within-step aggregation alone; "
        "retained-mass timing and transport discretization are material."
    )
    (AUDIT / "TIMESTEP_AUDIT.md").write_text(
        "# Timestep root-cause audit\n\n"
        "## Design and definitions\n\n"
        "The 1-h selected uniform, continuous-joint, and mapped-joint designs "
        "were reevaluated at 1.0 and 0.5 h using weather resampled from the same "
        "0.5-h master series. `L_max`, `S_max`, event count, and SSCI definitions "
        "were not changed. `S_max` remains the maximum mass released in one "
        "simulation interval and is therefore inseparable from its timestep.\n\n"
        "## Diagnostics\n\n"
        f"- Maximum forcing-total difference: {input_difference:.6g} kg m-1.\n"
        f"- Maximum relative change in total shed mass: "
        f"{100 * total_shed_relative:.3f}%.\n"
        f"- Maximum absolute relative change in `S_max`: "
        f"{100 * s_max_relative:.3f}%.\n"
        f"- Maximum absolute relative change in mean event count: "
        f"{100 * event_relative:.3f}%.\n"
        f"- Maximum absolute mass-balance error: "
        f"{maximum_balance_error:.6g} kg m-1.\n\n"
        "## Root cause\n\n"
        f"{mechanism}\n\n"
        "The failure is not repaired by redefining events or outcomes. It "
        "justifies rerunning production at the frozen 0.5-h reference "
        "resolution and continuing to report `S_max` with its interval.\n",
        encoding="utf-8",
    )


def _append_comparison(
    rows: list[dict],
    section: str,
    design_class: str,
    item: str,
    metric: str,
    old: float,
    new: float,
) -> None:
    rows.append(
        {
            "section": section,
            "design_class": design_class,
            "item": item,
            "metric": metric,
            "value_1h": old,
            "value_0p5h": new,
            "absolute_change": new - old,
            "relative_change": _relative_change(new, old),
        }
    )


def stage_comparison() -> None:
    rows: list[dict] = []
    old_baseline = pd.read_csv(REFERENCE / "baseline_aggregate.csv").set_index(
        "design"
    )
    new_baseline = pd.read_csv(RESULTS / "baseline_aggregate.csv").set_index(
        "design"
    )
    for design in old_baseline.index:
        for metric in TIMESTEP_METRICS:
            _append_comparison(
                rows,
                "baseline",
                "uniform_baseline",
                design,
                metric,
                float(old_baseline.loc[design, metric]),
                float(new_baseline.loc[design, metric]),
            )

    for design_class in ["uniform", "geometry", "surface", "joint"]:
        old = pd.read_csv(REFERENCE / f"{design_class}_pareto.csv")
        new = pd.read_csv(RESULTS / f"{design_class}_pareto.csv")
        old_unique = old[OBJECTIVES].round(6).drop_duplicates()
        new_unique = new[OBJECTIVES].round(6).drop_duplicates()
        summaries = {
            "nondominated_design_rows": (len(old), len(new)),
            "unique_objective_pairs": (len(old_unique), len(new_unique)),
            "minimum_l_max_kg_per_m": (
                old["l_max_kg_per_m"].min(),
                new["l_max_kg_per_m"].min(),
            ),
            "maximum_l_max_kg_per_m": (
                old["l_max_kg_per_m"].max(),
                new["l_max_kg_per_m"].max(),
            ),
            "minimum_s_max_kg_per_m": (
                old["s_max_kg_per_m"].min(),
                new["s_max_kg_per_m"].min(),
            ),
            "maximum_s_max_kg_per_m": (
                old["s_max_kg_per_m"].max(),
                new["s_max_kg_per_m"].max(),
            ),
        }
        for metric, (old_value, new_value) in summaries.items():
            _append_comparison(
                rows,
                "frontier",
                design_class,
                "complete_front",
                metric,
                float(old_value),
                float(new_value),
            )
        old_knee = _select_knee(old)
        new_knee = _select_knee(new)
        for metric in OBJECTIVES:
            _append_comparison(
                rows,
                "descriptive_knee",
                design_class,
                "front_specific_normalization",
                metric,
                float(old_knee[metric]),
                float(new_knee[metric]),
            )

    old_hypervolume = pd.read_csv(
        REFERENCE / "final_revision_frontier_metric_sensitivity.csv"
    )
    new_hypervolume = pd.read_csv(
        RESULTS / "final_revision_frontier_metric_sensitivity.csv"
    )
    for design_class in ["uniform", "geometry", "surface", "joint"]:
        old_row = old_hypervolume.loc[
            old_hypervolume["design_class"].eq(design_class)
            & old_hypervolume["normalization_origin"].eq("zero")
            & old_hypervolume["reference_margin"].eq(1.05)
        ].iloc[0]
        new_row = new_hypervolume.loc[
            new_hypervolume["design_class"].eq(design_class)
            & new_hypervolume["normalization_origin"].eq("zero")
            & new_hypervolume["reference_margin"].eq(1.05)
        ].iloc[0]
        _append_comparison(
            rows,
            "frontier_metric",
            design_class,
            "zero_origin_1p05_reference",
            "normalized_hypervolume_fraction",
            float(old_row["normalized_hypervolume_fraction"]),
            float(new_row["normalized_hypervolume_fraction"]),
        )

    old_constructability = pd.read_csv(
        REFERENCE / "final_revision_constructability_by_objective.csv"
    )
    new_constructability = pd.read_csv(
        RESULTS / "final_revision_constructability_by_objective.csv"
    )
    for design_class in ["uniform", "geometry", "surface", "joint"]:
        _append_comparison(
            rows,
            "constructability",
            design_class,
            "all_objective_groups",
            "feasible_design_rows",
            float(
                old_constructability.loc[
                    old_constructability["design_class"].eq(design_class),
                    "feasible_design_rows",
                ].sum()
            ),
            float(
                new_constructability.loc[
                    new_constructability["design_class"].eq(design_class),
                    "feasible_design_rows",
                ].sum()
            ),
        )

    old_mapping = pd.read_csv(
        REFERENCE / "final_revision_discretization_loss.csv"
    ).iloc[0]
    new_mapping = pd.read_csv(
        RESULTS / "final_revision_discretization_loss.csv"
    ).iloc[0]
    for metric in [
        "l_max_percent_change",
        "s_max_percent_change",
        "continuous_slope_transitions",
        "mapped_slope_transitions",
    ]:
        _append_comparison(
            rows,
            "constructability",
            "joint",
            "selected_knee_mapping",
            metric,
            float(old_mapping[metric]),
            float(new_mapping[metric]),
        )

    old_robustness = pd.read_csv(
        REFERENCE / "final_revision_objective_equivalent_robustness.csv"
    ).sort_values("candidate_count", ascending=False).iloc[0]
    new_robustness = pd.read_csv(
        RESULTS / "final_revision_objective_equivalent_robustness.csv"
    ).sort_values("candidate_count", ascending=False).iloc[0]
    for metric in [
        "candidate_count",
        "q95_l_min_kg_per_m",
        "q95_l_max_kg_per_m",
        "q95_s_min_kg_per_m",
        "q95_s_max_kg_per_m",
        "intervention_probability_min",
        "intervention_probability_max",
    ]:
        _append_comparison(
            rows,
            "robustness",
            "joint_and_uniform",
            "largest_objective_equivalent_group",
            metric,
            float(old_robustness[metric]),
            float(new_robustness[metric]),
        )
    _append_comparison(
        rows,
        "robustness",
        "joint_and_uniform",
        "minimum_score_tie",
        "candidate_count",
        float(
            len(
                pd.read_csv(
                    REFERENCE / "final_revision_robust_selection_ties.csv"
                )
            )
        ),
        float(
            len(
                pd.read_csv(
                    RESULTS / "final_revision_robust_selection_ties.csv"
                )
            )
        ),
    )

    old_jma = pd.read_csv(
        REFERENCE / "final_revision_jma_paired_summary.csv"
    ).set_index("metric")
    new_jma = pd.read_csv(
        RESULTS / "final_revision_jma_paired_summary.csv"
    ).set_index("metric")
    for metric in [
        "joint_to_uniform_l_max_ratio",
        "joint_to_uniform_s_max_ratio",
        "l_max_increase_percent",
        "s_max_reduction_percent",
    ]:
        _append_comparison(
            rows,
            "jma_scenario",
            "joint_vs_uniform",
            "station_winter_median",
            metric,
            float(old_jma.loc[metric, "median"]),
            float(new_jma.loc[metric, "median"]),
        )
    comparison = pd.DataFrame(rows)
    comparison.to_csv(RESULTS / "1h_vs_0p5h.csv", index=False)
    primary = comparison.loc[
        (
            comparison["section"].eq("baseline")
            & comparison["item"].eq("conventional_shedding")
            & comparison["metric"].isin(OBJECTIVES)
        )
        | (
            comparison["section"].eq("frontier")
            & comparison["design_class"].isin(["uniform", "joint"])
            & comparison["metric"].eq("unique_objective_pairs")
        )
        | (
            comparison["section"].eq("descriptive_knee")
            & comparison["design_class"].eq("joint")
        )
        | (
            comparison["section"].eq("frontier_metric")
            & comparison["design_class"].isin(["uniform", "joint"])
        )
        | (
            comparison["section"].eq("constructability")
            & comparison["design_class"].eq("joint")
            & comparison["metric"].isin(
                [
                    "feasible_design_rows",
                    "l_max_percent_change",
                    "s_max_percent_change",
                ]
            )
        )
        | (
            comparison["section"].eq("robustness")
            & comparison["metric"].isin(
                [
                    "candidate_count",
                    "q95_l_min_kg_per_m",
                    "q95_l_max_kg_per_m",
                    "q95_s_min_kg_per_m",
                    "q95_s_max_kg_per_m",
                ]
            )
        )
        | comparison["section"].eq("jma_scenario")
    ]
    audit_lines = [
        "# Old-versus-new primary audit",
        "",
        "The 0.5-h rerun retained nominal intermediate joint trade-offs, but fewer "
        "unique pairs remained and no joint row passed every post hoc constructability "
        "check. Mapping loss and the targeted 0.25-h sensitivity make "
        "constructability and interval dependence the dominant interpretation.",
        "",
        "| Section | Class | Item | Metric | 1 h | 0.5 h | Relative change |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in primary.itertuples(index=False):
        relative = (
            "NA"
            if pd.isna(row.relative_change)
            else f"{100 * row.relative_change:+.2f}%"
        )
        audit_lines.append(
            f"| {row.section} | {row.design_class} | {row.item} | "
            f"{row.metric} | {row.value_1h:.6g} | {row.value_0p5h:.6g} | "
            f"{relative} |"
        )
    audit_lines.extend(
        [
            "",
            "The complete machine-readable comparison is "
            "`results/generated/1h_vs_0p5h.csv`.",
        ]
    )
    (AUDIT / "OLD_VS_NEW_PRIMARY_AUDIT.md").write_text(
        "\n".join(audit_lines) + "\n",
        encoding="utf-8",
    )


def stage_quarter_hour() -> None:
    config = _config(ROOT / "config" / "production.yaml")
    production = float(config["simulation"]["dt_hours"])
    reference = float(
        config["convergence"]["post_freeze_reference_dt_hours"]
    )
    designs = _selected_designs(config, RESULTS)
    aggregate, _ = _aggregate_at_steps(
        config,
        designs,
        [production, reference],
    )
    metrics = [
        "l_max_kg_per_m",
        "s_max_kg_per_m",
        "mean_event_count",
        "mean_ssci",
    ]
    for _, indices in aggregate.groupby("design").groups.items():
        group = aggregate.loc[indices]
        reference_row = group.loc[group["dt_hours"].eq(reference)].iloc[0]
        for metric in metrics:
            denominator = max(abs(float(reference_row[metric])), 1e-12)
            aggregate.loc[indices, f"{metric}_relative_error"] = (
                aggregate.loc[indices, metric] - float(reference_row[metric])
            ).abs() / denominator
    error_columns = [f"{metric}_relative_error" for metric in metrics]
    aggregate["maximum_relative_error"] = aggregate[error_columns].max(axis=1)
    aggregate["within_frozen_tolerance"] = (
        aggregate["maximum_relative_error"]
        <= config["convergence"]["relative_tolerance"]
    )
    aggregate.to_csv(
        RESULTS / "final_revision_selected_design_0p25h_audit.csv",
        index=False,
    )
    production_rows = aggregate.loc[aggregate["dt_hours"].eq(production)]
    lines = [
        "# Post-freeze 0.25-hour numerical sensitivity",
        "",
        "The 0.5-h production designs were reevaluated at 0.25 h using the same "
        "forcing totals and unchanged outcome definitions. This is a targeted "
        "sensitivity check, not a second optimizer run and not a rule for "
        "recursively changing production resolution.",
        "",
        "| Design | L_max error | S_max error | Event-count error | SSCI error |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in production_rows.itertuples(index=False):
        lines.append(
            f"| {row.design} | "
            f"{100 * row.l_max_kg_per_m_relative_error:.3f}% | "
            f"{100 * row.s_max_kg_per_m_relative_error:.3f}% | "
            f"{100 * row.mean_event_count_relative_error:.3f}% | "
            f"{100 * row.mean_ssci_relative_error:.3f}% |"
        )
    lines.extend(
        [
            "",
            "`S_max` is interval-specific by definition. The 0.25-h result "
            "therefore constrains interpretation but does not redefine the "
            "frozen primary outcome or trigger a whole-optimizer rerun.",
            "",
        ]
    )
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "NUMERICAL_REFERENCE_AUDIT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    timestep = pd.read_csv(
        RESULTS / "final_revision_selected_design_timestep_audit.csv"
    )
    one_hour = timestep.loc[timestep["dt_hours"].eq(1.0)]
    quarter_failures = int(
        (~production_rows["within_frozen_tolerance"]).sum()
    )
    one_hour_failures = int((~one_hour["within_tolerance"]).sum())
    targeted_lines = [
        "# Targeted corrective analyses",
        "",
        "## Numerical resolution",
        "",
        f"All {one_hour_failures} selected-design 1-h rows fail the frozen "
        "composite criterion relative to 0.5 h. Production was therefore rerun "
        "at 0.5 h with unchanged outcomes, weather, parameter ranges, optimizer "
        "effort, constraints, seeds, and decision rules.",
        "",
        f"All {quarter_failures} selected 0.5-h rows fail the targeted frozen "
        "tolerance relative to 0.25 h. The 0.25-h calculation is disclosed as "
        "post-freeze sensitivity only; it neither reopens the optimizer nor "
        "supports a claim of convergence beyond the 0.5-h production reference.",
        "",
        "## Interpretation",
        "",
        "The 0.5-h joint front retains nominal intermediate objective pairs, "
        "but interval dependence and the failure of continuous joint rows under "
        "post hoc constructability checks dominate the practical interpretation. "
        "No outcome definition was changed to rescue the hypothesis.",
        "",
    ]
    targeted_path = (
        ROOT
        / "audit"
        / "final_revision"
        / "TARGETED_CORRECTIVE_ANALYSES.md"
    )
    targeted_path.parent.mkdir(parents=True, exist_ok=True)
    targeted_path.write_text(
        "\n".join(targeted_lines),
        encoding="utf-8",
    )


def stage_checkpoint_audit() -> None:
    config = _config(ROOT / "config" / "production.yaml")
    dt_token = str(config["simulation"]["dt_hours"]).replace(".", "p")
    checkpoint_dir = ROOT / "checkpoints" / f"dt_{dt_token}h"
    rows = []
    weathers = synthetic_weather_set(config)
    compatibility_keys = [
        "mode",
        "seed",
        "dt_hours",
        "population",
        "generations",
        "config_sha256",
        "weather_sha256",
        "source_sha256",
    ]
    for mode in ["geometry", "surface", "joint"]:
        for seed in config["optimizer"]["seeds"]:
            path = checkpoint_dir / f"{mode}_seed_{seed}.pkl"
            manifest_path = path.with_suffix(f"{path.suffix}.json")
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
            expected = _checkpoint_metadata(
                config,
                weathers,
                mode,
                int(seed),
            )
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            metadata_verified = all(
                manifest[key] == expected[key]
                for key in compatibility_keys
            )
            embedded_metadata_verified = True
            try:
                _load_checkpoint(path, expected)
            except (TypeError, ValueError):
                embedded_metadata_verified = False
            rows.append(
                {
                    "checkpoint": str(path.relative_to(ROOT)),
                    "manifest": str(manifest_path.relative_to(ROOT)),
                    **{
                        key: manifest[key]
                        for key in compatibility_keys
                    },
                    "code_commit": manifest["code_commit"],
                    "checkpoint_sha256": checksum,
                    "checksum_verified": (
                        checksum == manifest["checkpoint_sha256"]
                    ),
                    "metadata_verified": metadata_verified,
                    "embedded_metadata_verified": (
                        embedded_metadata_verified
                    ),
                    "integrity_verified": (
                        checksum == manifest["checkpoint_sha256"]
                        and metadata_verified
                        and embedded_metadata_verified
                    ),
                }
            )
    audit = pd.DataFrame(rows)
    expected = 3 * len(config["optimizer"]["seeds"])
    if len(audit) != expected or not audit["integrity_verified"].all():
        raise ValueError("0.5-h checkpoint audit failed")
    audit.to_csv(
        ROOT / "audit" / "0p5h_revision" / "checkpoint_audit.csv",
        index=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=[
            "timestep",
            "comparison",
            "quarter-hour",
            "checkpoint-audit",
        ],
        required=True,
    )
    args = parser.parse_args()
    if args.stage == "timestep":
        stage_timestep()
    elif args.stage == "comparison":
        stage_comparison()
    elif args.stage == "quarter-hour":
        stage_quarter_hour()
    else:
        stage_checkpoint_audit()


if __name__ == "__main__":
    main()
