from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from graded_roof.complexity import design_complexity, manufacturable_mapping
from graded_roof.study import (
    evaluate_design,
    heterogeneous_design,
    simulation_config,
    synthetic_weather_set,
    uniform_design,
)

FIGURE_FORMATS = [
    ("png", ".png", 300),
    ("tiff", ".tiff", 1000),
    ("vector", ".svg", 300),
    ("vector", ".pdf", 300),
    ("vector", ".eps", 300),
]


def select_knee(front: pd.DataFrame) -> pd.Series:
    objectives = front[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy()
    span = np.ptp(objectives, axis=0)
    normalized = (objectives - objectives.min(axis=0)) / np.where(
        span > 0,
        span,
        1.0,
    )
    return front.iloc[int(np.argmin(np.linalg.norm(normalized, axis=1)))]


def design_from_row(row: pd.Series, config: dict, mode: str):
    columns = sorted(
        (column for column in row.index if column.startswith("x_")),
        key=lambda column: int(column.split("_", maxsplit=1)[1]),
    )
    return heterogeneous_design(
        row[columns].to_numpy(dtype=float),
        config,
        mode,
        label=f"{mode}_knee",
    )


def design_for_front_row(row: pd.Series, config: dict, mode: str):
    if mode == "uniform":
        return uniform_design(
            config,
            float(row["slope_deg"]),
            float(row["mu_static"]),
            float(row["adhesion_pa"]),
            label="uniform",
        )
    return design_from_row(row, config, mode)


def classify_strategy(
    design_class: str,
    design,
    metrics: pd.Series | dict,
    config: dict,
) -> str:
    thresholds = config["classification"]
    shed_fraction = float(metrics["mean_total_shed_kg_per_m"]) / max(
        float(metrics["mean_input_snow_kg_per_m"]),
        1e-12,
    )
    residual_fraction = float(metrics["mean_residual_mass_kg_per_m"]) / max(
        float(metrics["mean_input_snow_kg_per_m"]),
        1e-12,
    )
    if shed_fraction <= thresholds["retention_shed_fraction_threshold"]:
        return "RETENTION"
    if residual_fraction <= thresholds["shedding_residual_fraction_threshold"]:
        return "SHEDDING"
    if design_class == "uniform":
        return "UNIFORM_INTERMEDIATE"
    slope_span = np.ptp(config["roof"]["slope_bounds_deg"])
    friction_span = np.ptp(config["surface"]["static_friction_bounds"])
    heterogeneity = max(
        float(np.std(design.slope_deg) / slope_span),
        float(np.std(design.mu_static) / friction_span),
    )
    if heterogeneity >= thresholds["heterogeneity_sd_threshold"]:
        return "GRADED_HYBRID"
    return "UNIFORM_INTERMEDIATE"


def generate_tables(config: dict, root: Path) -> None:
    results = root / config["project"]["results_dir"]
    tables = root / config["project"]["tables_dir"]
    tables.mkdir(parents=True, exist_ok=True)
    fronts = {
        "uniform": pd.read_csv(results / "uniform_pareto.csv"),
        "geometry": pd.read_csv(results / "geometry_pareto.csv"),
        "surface": pd.read_csv(results / "surface_pareto.csv"),
        "joint": pd.read_csv(results / "joint_pareto.csv"),
    }
    frontier_summary = pd.read_csv(
        results / "final_revision_frontier_summary.csv"
    )
    hypervolume = pd.read_csv(
        results / "final_revision_frontier_metric_sensitivity.csv"
    )
    hypervolume = hypervolume.loc[
        hypervolume["normalization_origin"].eq("zero")
        & hypervolume["reference_margin"].eq(1.05),
        ["design_class", "normalized_hypervolume_fraction"],
    ]
    knees = pd.read_csv(results / "final_revision_knee_audit.csv")
    knees = knees.loc[
        knees["normalization"].eq("front_specific_minmax"),
        ["design_class", "l_max_kg_per_m", "s_max_kg_per_m"],
    ].rename(
        columns={
            "l_max_kg_per_m": "descriptive_knee_l_max_kg_per_m",
            "s_max_kg_per_m": "descriptive_knee_s_max_kg_per_m",
        }
    )
    frontier_table = frontier_summary.merge(
        hypervolume,
        on="design_class",
        validate="one_to_one",
    ).merge(
        knees,
        on="design_class",
        validate="one_to_one",
    ).rename(
        columns={
            "additive_epsilon_vs_uniform_common_minmax": (
                "additive_epsilon_vs_uniform"
            )
        }
    )
    frontier_table.to_csv(
        tables / "table_1_pareto_summary.csv",
        index=False,
    )

    joint_row = select_knee(fronts["joint"])
    continuous = design_from_row(joint_row, config, "joint")
    classes = config["surface"]["discrete_classes"]
    discrete, class_labels = manufacturable_mapping(
        continuous,
        classes,
        slope_rounding_deg=config["complexity"]["slope_rounding_deg"],
        minimum_segment_cells=config["roof"]["minimum_segment_cells"],
        maximum_transitions=config["roof"]["maximum_transitions"],
        maximum_adjacent_slope_change_deg=config["roof"][
            "adjacent_slope_limit_deg"
        ],
    )
    profile = pd.DataFrame(
        {
            "cell": np.arange(1, continuous.cells + 1),
            "continuous_slope_deg": continuous.slope_deg,
            "discrete_slope_deg": discrete.slope_deg,
            "continuous_mu_static": continuous.mu_static,
            "continuous_adhesion_pa": continuous.adhesion_pa,
            "discrete_material_class": class_labels,
            "discrete_mu_static": discrete.mu_static,
            "discrete_adhesion_pa": discrete.adhesion_pa,
        }
    )
    profile.to_csv(tables / "table_2_selected_profile.csv", index=False)
    settings = simulation_config(config)
    weathers = synthetic_weather_set(config)
    continuous_metrics, _ = evaluate_design(continuous, weathers, settings)
    discrete_metrics, _ = evaluate_design(discrete, weathers, settings)
    mapping_table = pd.DataFrame(
        [
            {
                "mapping": "continuous",
                **continuous_metrics,
                "l_max_discretization_loss": 0.0,
                "s_max_discretization_loss": 0.0,
            },
            {
                "mapping": "manufacturable_discrete_generic_classes",
                **discrete_metrics,
                "l_max_discretization_loss": (
                    float(discrete_metrics["l_max_kg_per_m"])
                    - float(continuous_metrics["l_max_kg_per_m"])
                ),
                "s_max_discretization_loss": (
                    float(discrete_metrics["s_max_kg_per_m"])
                    - float(continuous_metrics["s_max_kg_per_m"])
                ),
            },
        ]
    )
    continuous_row = mapping_table.iloc[0]
    mapping_table["l_max_change_kg_per_m"] = (
        mapping_table["l_max_kg_per_m"]
        - continuous_row["l_max_kg_per_m"]
    )
    mapping_table["s_max_change_kg_per_m"] = (
        mapping_table["s_max_kg_per_m"]
        - continuous_row["s_max_kg_per_m"]
    )
    mapping_table["l_max_change_percent"] = (
        100.0
        * mapping_table["l_max_change_kg_per_m"]
        / max(abs(float(continuous_row["l_max_kg_per_m"])), 1e-12)
    )
    mapping_table["s_max_change_percent"] = (
        100.0
        * mapping_table["s_max_change_kg_per_m"]
        / max(abs(float(continuous_row["s_max_kg_per_m"])), 1e-12)
    )
    mapping_table.to_csv(
        tables / "table_3_discretization.csv",
        index=False,
    )

    complexity_rows = []
    for design_class, frame in fronts.items():
        for row_index, row in frame.iterrows():
            design = design_for_front_row(row, config, design_class)
            complexity = design_complexity(
                design,
                classes,
                slope_rounding_deg=config["complexity"]["slope_rounding_deg"],
            )
            complexity_rows.append(
                {
                    "design_class": design_class,
                    "front_row": row_index,
                    "l_max_kg_per_m": row["l_max_kg_per_m"],
                    "s_max_kg_per_m": row["s_max_kg_per_m"],
                    **complexity,
                    "meets_adjacent_slope_limit": (
                        complexity["maximum_adjacent_slope_change_deg"]
                        <= config["roof"]["adjacent_slope_limit_deg"]
                    ),
                    "meets_minimum_segment_length": (
                        complexity["minimum_segment_cells"]
                        >= config["roof"]["minimum_segment_cells"]
                    ),
                    "meets_maximum_transitions": (
                        complexity["transition_count"]
                        <= config["roof"]["maximum_transitions"]
                    ),
                }
            )

    candidates = pd.concat(
        [
            fronts["uniform"].assign(design_class="uniform"),
            fronts["joint"].assign(design_class="joint"),
        ],
        ignore_index=True,
    )
    candidate_records = []
    for candidate_index, row in candidates.iterrows():
        candidate_records.append(
            (
                candidate_index,
                row["design_class"],
                design_for_front_row(row, config, row["design_class"]),
                row.to_dict(),
            )
        )
    base_weathers = synthetic_weather_set(config)
    phase_metrics = []
    for snowfall_factor in config["phase_diagram"]["snowfall_factors"]:
        scenario_weathers = [
            replace(
                weather,
                snowfall_kg_m2=weather.snowfall_kg_m2 * snowfall_factor,
                name=f"{weather.name}_snowfall_{snowfall_factor:g}",
            )
            for weather in base_weathers
        ]
        for (
            candidate_index,
            design_class,
            design,
            nominal_metrics,
        ) in candidate_records:
            if np.isclose(snowfall_factor, 1.0):
                metrics = nominal_metrics
            else:
                metrics, _ = evaluate_design(
                    design,
                    scenario_weathers,
                    settings,
                )
            phase_metrics.append(
                {
                    "candidate_index": candidate_index,
                    "snowfall_factor": snowfall_factor,
                    "design_class": design_class,
                    **metrics,
                    "design_object": design,
                }
            )
    phase_rows = []
    phase_frame = pd.DataFrame(phase_metrics)
    for snowfall_factor, scenario in phase_frame.groupby("snowfall_factor"):
        objectives = scenario[
            [
                "l_max_kg_per_m",
                "s_max_kg_per_m",
                "mean_manual_triggers",
            ]
        ]
        span = objectives.max() - objectives.min()
        normalized = (objectives - objectives.min()) / span.replace(0, 1)
        for shedding_weight in config["decision"]["shedding_penalty_weights"]:
            for (
                labor_label,
                labor_weight,
            ) in config["decision"]["labor_scarcity_weights"].items():
                score = (
                    normalized["l_max_kg_per_m"]
                    + shedding_weight * normalized["s_max_kg_per_m"]
                    + labor_weight * normalized["mean_manual_triggers"]
                )
                for allowable in config["decision"]["allowable_shed_kg_per_m"]:
                    feasible = scenario["s_max_kg_per_m"] <= allowable
                    constrained_score = score.where(feasible, np.inf)
                    constraint_feasible = bool(feasible.any())
                    selected_index = (
                        int(constrained_score.idxmin())
                        if constraint_feasible
                        else int(scenario["s_max_kg_per_m"].idxmin())
                    )
                    selected = scenario.loc[selected_index]
                    design = selected["design_object"]
                    phase_rows.append(
                        {
                            "snowfall_factor": snowfall_factor,
                            "shedding_penalty_weight": shedding_weight,
                            "labor_scarcity": labor_label,
                            "manual_intervention_weight": labor_weight,
                            "allowable_shed_kg_per_m": allowable,
                            "constraint_feasible": constraint_feasible,
                            "selected_design_class": selected["design_class"],
                            "strategy": classify_strategy(
                                selected["design_class"],
                                design,
                                selected,
                                config,
                            ),
                            "l_max_kg_per_m": selected["l_max_kg_per_m"],
                            "s_max_kg_per_m": selected["s_max_kg_per_m"],
                            "mean_manual_triggers": selected[
                                "mean_manual_triggers"
                            ],
                            "mean_ssci": selected["mean_ssci"],
                        }
                    )
    phase_table = pd.DataFrame(phase_rows)
    phase_table.to_csv(
        tables / "table_4_strategy_phase_diagram.csv",
        index=False,
    )
    labor_table = phase_table.loc[
        (phase_table["snowfall_factor"] == 1.0)
        & (phase_table["shedding_penalty_weight"] == 1.0)
        & (
            phase_table["allowable_shed_kg_per_m"]
            == max(config["decision"]["allowable_shed_kg_per_m"])
        )
    ].copy()
    labor_table.to_csv(
        tables / "table_5_labor_scarcity.csv",
        index=False,
    )
    jma_path = results / "jma_daily_evaluation.csv"
    if jma_path.exists():
        pd.read_csv(
            results / "final_revision_jma_paired_tradeoffs.csv"
        ).to_csv(
            tables / "table_9_jma_daily_evaluation.csv",
            index=False,
        )
    complexity_frame = pd.DataFrame(complexity_rows)
    objective_values = complexity_frame[["l_max_kg_per_m", "s_max_kg_per_m"]]
    normalized = (objective_values - objective_values.min()) / (
        objective_values.max() - objective_values.min()
    ).replace(0, 1)
    complexity_frame["complexity_penalized_score"] = (
        normalized["l_max_kg_per_m"]
        + normalized["s_max_kg_per_m"]
        + config["complexity"]["transition_penalty_base"]
        * complexity_frame["transition_count"]
        / max(config["roof"]["maximum_transitions"], 1)
    )
    complexity_frame.to_csv(
        tables / "table_6_complexity_analysis.csv",
        index=False,
    )
    penalty_rows = []
    for penalty in config["complexity"]["transition_penalties"]:
        score = (
            normalized["l_max_kg_per_m"]
            + normalized["s_max_kg_per_m"]
            + penalty
            * complexity_frame["transition_count"]
            / max(config["roof"]["maximum_transitions"], 1)
        )
        selected = complexity_frame.loc[score.idxmin()]
        penalty_rows.append(
            {
                "transition_penalty": penalty,
                **selected.to_dict(),
                "selection_score": score.loc[selected.name],
            }
        )
    pd.DataFrame(penalty_rows).to_csv(
        tables / "table_7_complexity_penalty.csv",
        index=False,
    )
    robustness_summary = (
        results / "final_revision_robustness_candidate_audit.csv"
    )
    if robustness_summary.exists():
        pd.read_csv(robustness_summary).to_csv(
            tables / "table_8_robustness_summary.csv",
            index=False,
        )
    pd.read_csv(results / "optimizer_stochasticity.csv").to_csv(
        tables / "supplement_optimizer_stochasticity.csv",
        index=False,
    )


def _save_figure(figure: plt.Figure, root: Path, stem: str) -> None:
    for folder, suffix, dpi in FIGURE_FORMATS:
        destination = root / "figures" / folder
        destination.mkdir(parents=True, exist_ok=True)
        options = (
            {"pil_kwargs": {"compression": "tiff_lzw"}}
            if suffix == ".tiff"
            else {}
        )
        figure.savefig(
            destination / f"{stem}{suffix}",
            dpi=dpi,
            bbox_inches="tight",
            **options,
        )
    plt.close(figure)


def generate_figures(config: dict, root: Path) -> None:
    results = root / config["project"]["results_dir"]
    tables = root / config["project"]["tables_dir"]
    for folder, suffix, _ in FIGURE_FORMATS:
        destination = root / "figures" / folder
        destination.mkdir(parents=True, exist_ok=True)
        for existing in destination.glob(f"*{suffix}"):
            existing.unlink()
    baselines = pd.read_csv(results / "baseline_aggregate.csv")
    uniform = pd.read_csv(results / "uniform_pareto.csv")
    geometry = pd.read_csv(results / "geometry_pareto.csv")
    surface = pd.read_csv(results / "surface_pareto.csv")
    joint = pd.read_csv(results / "joint_pareto.csv")
    profile = pd.read_csv(tables / "table_2_selected_profile.csv")

    def objective_pairs(frame: pd.DataFrame) -> pd.DataFrame:
        pair_columns = ["l_max_kg_per_m", "s_max_kg_per_m"]
        rounded = frame[pair_columns].round(6)
        return frame.loc[~rounded.duplicated()].sort_values(pair_columns)

    figure, axis = plt.subplots(figsize=(8.5, 4.0))
    axis.axis("off")
    stages = [
        ("Weather forcing", "snowfall, temperature,\nrain-on-snow"),
        ("Cell states", "mass, age, volume,\ndensity"),
        ("Threshold transport", "static release,\nkinetic transfer"),
        ("Study outcomes", r"$L_{\max}$, $S_{\max}$," + "\nSSCI and diagnostics"),
    ]
    x_positions = np.linspace(0.13, 0.87, len(stages))
    for index, ((title, detail), x_position) in enumerate(
        zip(stages, x_positions, strict=True)
    ):
        axis.text(
            x_position,
            0.55,
            f"{title}\n{detail}",
            ha="center",
            va="center",
            transform=axis.transAxes,
            bbox={
                "boxstyle": "round,pad=0.5",
                "facecolor": "#f3f6f8",
                "edgecolor": "#4c566a",
            },
        )
        if index < len(stages) - 1:
            axis.annotate(
                "",
                xy=(x_positions[index + 1] - 0.09, 0.55),
                xytext=(x_position + 0.09, 0.55),
                xycoords=axis.transAxes,
                arrowprops={"arrowstyle": "->", "color": "#4c566a"},
            )
    axis.text(
        0.5,
        0.15,
        "Uniform grid search and multi-seed heterogeneous NSGA-II use identical "
        "modeled environments",
        ha="center",
        transform=axis.transAxes,
    )
    _save_figure(figure, root, "figure_1_conceptual_model")

    synthetic_paths = sorted(
        (root / "data" / "processed" / "synthetic").glob("*.csv")
    )
    jma_observations = pd.read_csv(
        root / "data" / "processed" / "jma_daily_observations.csv"
    )
    figure, axes = plt.subplots(1, 2, figsize=(9.5, 4.0))
    for path in synthetic_paths:
        weather = pd.read_csv(path)
        axes[0].plot(
            weather["time_h"] / 24.0,
            weather["snowfall_kg_m2"].cumsum(),
            label=path.stem.replace("_", " "),
        )
    axes[0].set(
        xlabel="Modeled time (days)",
        ylabel=r"Cumulative snowfall mass (kg m$^{-2}$)",
    )
    axes[0].legend(frameon=False, fontsize=7)
    jma_observations["winter"] = np.where(
        pd.to_datetime(jma_observations["date"]).dt.month
        >= config["jma"]["season_start_month"],
        pd.to_datetime(jma_observations["date"]).dt.year,
        pd.to_datetime(jma_observations["date"]).dt.year - 1,
    )
    jma_maximum = (
        jma_observations.groupby(["station_id", "winter"], as_index=False)[
            "ground_snow_depth_cm"
        ]
        .max()
        .dropna()
    )
    station_names = {
        station["id"]: station["name"]
        for station in config["jma"]["stations"]
    }
    for station_id, group in jma_maximum.groupby("station_id"):
        axes[1].plot(
            group["winter"].astype(str),
            group["ground_snow_depth_cm"],
            marker="o",
            label=station_names[station_id],
        )
    axes[1].set(
        xlabel="Winter starting year",
        ylabel="Observed ground snow depth (cm)",
    )
    axes[1].legend(frameon=False, fontsize=7)
    _save_figure(figure, root, "figure_2_weather_scenarios")

    figure, axes = plt.subplots(3, 1, figsize=(7.5, 7.0), sharex=True)
    axes[0].plot(
        profile["cell"],
        profile["continuous_slope_deg"],
        color="#1f77b4",
        label="Continuous",
    )
    axes[0].step(
        profile["cell"],
        profile["discrete_slope_deg"],
        where="mid",
        color="#ff7f0e",
        label="Post hoc mapped",
    )
    axes[1].plot(
        profile["cell"],
        profile["continuous_mu_static"],
        color="#d62728",
        label="Continuous",
    )
    axes[1].step(
        profile["cell"],
        profile["discrete_mu_static"],
        where="mid",
        color="#9467bd",
        label="Post hoc mapped",
    )
    class_codes, class_labels = pd.factorize(
        profile["discrete_material_class"],
        sort=True,
    )
    axes[2].step(
        profile["cell"],
        class_codes,
        where="mid",
        color="#2ca02c",
    )
    axes[0].set_ylabel("Slope (degrees)")
    axes[1].set_ylabel("Static friction")
    axes[2].set(
        xlabel="Ridge-to-eave cell",
        ylabel="Post hoc class",
        yticks=np.arange(len(class_labels)),
        yticklabels=class_labels,
    )
    axes[0].legend(frameon=False, ncol=2)
    axes[1].legend(frameon=False, ncol=2)
    figure.tight_layout()
    _save_figure(figure, root, "figure_4_selected_graded_profile")

    uniform_pairs = objective_pairs(uniform)
    joint_pairs = objective_pairs(joint)
    figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.4))
    for axis in axes:
        axis.plot(
            uniform_pairs["l_max_kg_per_m"],
            uniform_pairs["s_max_kg_per_m"],
            marker="s",
            linestyle="--",
            color="#4c78a8",
            label="Exhaustive uniform",
        )
        axis.plot(
            joint_pairs["l_max_kg_per_m"],
            joint_pairs["s_max_kg_per_m"],
            marker="o",
            color="#e45756",
            label="Joint heterogeneous",
        )
        axis.scatter(
            baselines["l_max_kg_per_m"],
            baselines["s_max_kg_per_m"],
            marker="x",
            s=55,
            color="black",
            label="Baselines",
        )
        axis.set(
            xlabel=r"Maximum modeled roof snow mass, $L_{\max}$ (kg m$^{-1}$)",
            ylabel=r"Maximum one-step release mass, $S_{\max}$ (kg m$^{-1}$)",
        )
    axes[0].set_title("Full objective range")
    axes[1].set_title("Intermediate trade-off region")
    intermediate = joint_pairs.loc[
        ~joint_pairs["l_max_kg_per_m"].isin(
            uniform_pairs["l_max_kg_per_m"]
        )
    ]
    axes[1].set_xlim(
        max(0.0, float(intermediate["l_max_kg_per_m"].min()) * 0.8),
        float(intermediate["l_max_kg_per_m"].max()) * 1.08,
    )
    axes[1].set_ylim(
        0.0,
        float(intermediate["s_max_kg_per_m"].max()) * 1.25,
    )
    axes[0].legend(frameon=False, fontsize=8)
    figure.tight_layout()
    _save_figure(figure, root, "figure_3_primary_pareto_comparison")

    figure, axis = plt.subplots(figsize=(6.5, 5.0))
    for label, frame, color in [
        ("geometry only", geometry, "#2ca02c"),
        ("surface only", surface, "#ff7f0e"),
        ("joint", joint, "#9467bd"),
        ("uniform", uniform, "#7f7f7f"),
    ]:
        pairs = objective_pairs(frame)
        axis.plot(
            pairs["l_max_kg_per_m"],
            pairs["s_max_kg_per_m"],
            marker="o",
            markersize=4,
            linewidth=1,
            color=color,
            label=label,
        )
    axis.set(
        xlabel=r"$L_{\max}$ (kg m$^{-1}$)",
        ylabel=r"$S_{\max}$ (kg m$^{-1}$)",
    )
    axis.legend(frameon=False)
    _save_figure(figure, root, "figure_5_ablation_pareto_fronts")

    convergence = pd.read_csv(results / "convergence.csv")
    figure, axes = plt.subplots(2, 2, figsize=(9.0, 7.0), sharex=True)
    for axis, objective, title in [
        (axes[0, 0], "l_max_kg_per_m_relative_error", r"$L_{\max}$"),
        (axes[0, 1], "s_max_kg_per_m_relative_error", r"$S_{\max}$"),
        (axes[1, 0], "mean_event_count_relative_error", "Event count"),
        (axes[1, 1], "mean_ssci_relative_error", "SSCI"),
    ]:
        for cells, group in convergence.groupby("cells"):
            axis.plot(
                group["dt_hours"],
                group[objective],
                marker="o",
                label=f"{cells} cells",
            )
        axis.axhline(
            config["convergence"]["relative_tolerance"],
            color="black",
            linestyle="--",
            linewidth=1,
        )
        production = convergence.loc[
            convergence["cells"].eq(config["roof"]["cells"])
            & convergence["dt_hours"].eq(config["simulation"]["dt_hours"])
        ].iloc[0]
        axis.scatter(
            production["dt_hours"],
            production[objective],
            marker="D",
            s=45,
            facecolor="white",
            edgecolor="black",
            zorder=5,
        )
        axis.set(xlabel="Time step (h)", ylabel="Relative error", title=title)
    axes[0, 1].legend(frameon=False)
    figure.suptitle("Relative difference from 48-cell, 0.5-h reference")
    figure.tight_layout()
    _save_figure(figure, root, "figure_6_numerical_convergence")

    sensitivity = pd.read_csv(results / "sensitivity.csv")
    sensitivity["relative_l_change"] = (
        sensitivity["l_max_kg_per_m"]
        - sensitivity["baseline_l_max_kg_per_m"]
    ) / sensitivity["baseline_l_max_kg_per_m"]
    sensitivity["relative_s_change"] = (
        sensitivity["s_max_kg_per_m"]
        - sensitivity["baseline_s_max_kg_per_m"]
    ) / sensitivity["baseline_s_max_kg_per_m"]
    sensitivity["axis_label"] = sensitivity.apply(
        lambda row: f"{row['dimension']} ({row['level']}={row['factor']:g})",
        axis=1,
    )
    plotted = sensitivity.sort_values(
        ["dimension", "level"],
        ascending=[True, False],
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.0, 8.0), sharey=True)
    y = np.arange(len(plotted))
    for axis, column, title, color in [
        (axes[0], "relative_l_change", r"$L_{\max}$", "#4c78a8"),
        (axes[1], "relative_s_change", r"$S_{\max}$", "#e45756"),
    ]:
        axis.barh(y, plotted[column], color=color)
        axis.axvline(0.0, color="black", linewidth=0.8)
        axis.set(
            xlabel="Relative change from baseline",
            title=title,
            yticks=y,
            yticklabels=plotted["axis_label"],
        )
    axes[1].tick_params(labelleft=False)
    figure.suptitle(
        "Prespecified low/high factors or encoded alternatives"
    )
    figure.tight_layout()
    _save_figure(figure, root, "figure_7_sensitivity")

    robustness = pd.read_csv(
        results / "final_revision_robustness_candidate_audit.csv"
    ).sort_values(["design_class", "quantile_l_max_kg_per_m"])
    figure, axes = plt.subplots(1, 2, figsize=(10.5, 7.0), sharey=True)
    y = np.arange(len(robustness))
    colors = robustness["design_class"].map(
        {"uniform": "#4c78a8", "joint": "#e45756"}
    )
    for axis, column, title in [
        (axes[0], "quantile_l_max_kg_per_m", "Q95 Lmax"),
        (axes[1], "quantile_s_max_kg_per_m", "Q95 Smax"),
    ]:
        axis.scatter(robustness[column], y, c=colors, s=30)
        axis.set_xscale("symlog", linthresh=10)
        axis.set(xlabel=f"{title} (kg m$^{{-1}}$)", yticks=y)
    axes[0].set_yticklabels(robustness["candidate_id"])
    axes[1].tick_params(labelleft=False)
    axes[0].scatter([], [], color="#4c78a8", label="Uniform")
    axes[0].scatter([], [], color="#e45756", label="Joint")
    axes[0].legend(frameon=False)
    figure.suptitle(
        "Candidate upper-tail outcomes under paired perturbation draws"
    )
    figure.tight_layout()
    _save_figure(figure, root, "figure_8_monte_carlo_robustness")

    labor = pd.read_csv(tables / "table_5_labor_scarcity.csv")
    labor = labor.loc[labor["labor_scarcity"].isin(["low", "medium", "high"])]
    phase = pd.read_csv(tables / "table_4_strategy_phase_diagram.csv")
    figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.5))
    scarcity_order = ["low", "medium", "high"]
    labor["labor_scarcity"] = pd.Categorical(
        labor["labor_scarcity"],
        categories=scarcity_order,
        ordered=True,
    )
    labor = labor.sort_values("labor_scarcity")
    x = np.arange(len(labor))
    axes[0].plot(
        x,
        labor["l_max_kg_per_m"],
        marker="o",
        label=r"$L_{\max}$",
    )
    axes[0].plot(
        x,
        labor["s_max_kg_per_m"],
        marker="s",
        linestyle="--",
        label=r"$S_{\max}$",
    )
    axes[0].set(
        xlabel="Labor-scarcity weight",
        ylabel=r"Selected objective (kg m$^{-1}$)",
        title="Frozen base decision scenario",
        xticks=x,
        xticklabels=labor["labor_scarcity"],
    )
    axes[0].legend(frameon=False)
    colors = {
        "RETENTION": "#1f77b4",
        "UNIFORM_INTERMEDIATE": "#7f7f7f",
        "SHEDDING": "#d62728",
        "GRADED_HYBRID": "#9467bd",
    }
    phase_counts = (
        phase.groupby(
            ["strategy", "l_max_kg_per_m", "s_max_kg_per_m"],
            as_index=False,
        )
        .size()
        .rename(columns={"size": "selection_count"})
    )
    for strategy, group in phase_counts.groupby("strategy"):
        axes[1].scatter(
            group["l_max_kg_per_m"],
            group["s_max_kg_per_m"],
            s=20 + 8 * group["selection_count"],
            alpha=0.75,
            color=colors[strategy],
            label=strategy.replace("_", " ").title(),
        )
    axes[1].set(
        xlabel=r"$L_{\max}$ (kg m$^{-1}$)",
        ylabel=r"$S_{\max}$ (kg m$^{-1}$)",
        title="Phase-diagram selections",
    )
    axes[1].legend(frameon=False, fontsize=7)
    _save_figure(figure, root, "figure_9_decision_phase_diagram")
