from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from graded_roof.complexity import design_complexity, manufacturable_mapping
from graded_roof.metrics import (
    additive_epsilon_indicator,
    matched_objective_improvement,
    nondominated_mask,
    normalized_hypervolume_2d,
)
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
    all_objectives = pd.concat(
        [
            frame[["l_max_kg_per_m", "s_max_kg_per_m"]]
            for frame in fronts.values()
        ],
        ignore_index=True,
    )
    reference = (
        float(all_objectives["l_max_kg_per_m"].max() * 1.05),
        float(all_objectives["s_max_kg_per_m"].max() * 1.05),
    )
    objective_minimum = all_objectives.min().to_numpy(float)
    objective_span = np.ptp(all_objectives.to_numpy(float), axis=0)
    objective_span = np.where(objective_span > 0, objective_span, 1.0)
    normalized_uniform = (
        fronts["uniform"][["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy()
        - objective_minimum
    ) / objective_span
    labeled_fronts = pd.concat(
        [
            frame.assign(design_class=name)
            for name, frame in fronts.items()
        ],
        ignore_index=True,
    )
    globally_nondominated = nondominated_mask(
        labeled_fronts[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy()
    )
    labeled_fronts["globally_nondominated"] = globally_nondominated
    summaries = []
    for name, frame in fronts.items():
        knee = select_knee(frame)
        normalized_front = (
            frame[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy()
            - objective_minimum
        ) / objective_span
        matched = matched_objective_improvement(
            frame[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy(),
            fronts["uniform"][
                ["l_max_kg_per_m", "s_max_kg_per_m"]
            ].to_numpy(),
        )
        class_global = labeled_fronts.loc[
            labeled_fronts["design_class"] == name,
            "globally_nondominated",
        ]
        summaries.append(
            {
                "design_class": name,
                "pareto_designs": len(frame),
                "minimum_l_max_kg_per_m": frame["l_max_kg_per_m"].min(),
                "minimum_s_max_kg_per_m": frame["s_max_kg_per_m"].min(),
                "knee_l_max_kg_per_m": knee["l_max_kg_per_m"],
                "knee_s_max_kg_per_m": knee["s_max_kg_per_m"],
                "normalized_hypervolume": normalized_hypervolume_2d(
                    frame[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy(),
                    reference,
                ),
                "additive_epsilon_vs_uniform": additive_epsilon_indicator(
                    normalized_front,
                    normalized_uniform,
                ),
                "dominated_fraction_in_combined_set": (
                    1.0 - float(class_global.mean())
                ),
                **matched,
            }
        )
    pd.DataFrame(summaries).to_csv(
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
    pd.DataFrame(
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
    ).to_csv(tables / "table_3_discretization.csv", index=False)

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
        pd.read_csv(jma_path).to_csv(
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
    robustness_summary = results / "robustness_summary.csv"
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
    for station_id, group in jma_maximum.groupby("station_id"):
        axes[1].plot(
            group["winter"].astype(str),
            group["ground_snow_depth_cm"],
            marker="o",
            label=station_id,
        )
    axes[1].set(
        xlabel="Winter starting year",
        ylabel="Observed ground snow depth (cm)",
    )
    axes[1].legend(frameon=False, fontsize=7)
    _save_figure(figure, root, "figure_2_weather_scenarios")

    figure, axis_left = plt.subplots(figsize=(7.2, 4.5))
    axis_right = axis_left.twinx()
    axis_left.plot(
        profile["cell"],
        profile["continuous_slope_deg"],
        color="#1f77b4",
        label="slope",
    )
    axis_right.plot(
        profile["cell"],
        profile["continuous_mu_static"],
        color="#d62728",
        label="static friction",
    )
    axis_left.set(xlabel="Ridge-to-eave cell", ylabel="Slope (degrees)")
    axis_right.set_ylabel("Static friction coefficient")
    figure.legend(loc="upper center", ncol=2, frameon=False)
    _save_figure(figure, root, "figure_4_selected_graded_profile")

    figure, axis = plt.subplots(figsize=(6.5, 5.0))
    axis.scatter(
        uniform["l_max_kg_per_m"],
        uniform["s_max_kg_per_m"],
        s=12,
        alpha=0.5,
        label="optimized uniform",
    )
    axis.scatter(
        joint["l_max_kg_per_m"],
        joint["s_max_kg_per_m"],
        s=14,
        alpha=0.7,
        label="joint heterogeneous",
    )
    axis.scatter(
        baselines["l_max_kg_per_m"],
        baselines["s_max_kg_per_m"],
        marker="x",
        s=65,
        color="black",
        label="baselines",
    )
    axis.set(
        xlabel=r"Maximum modeled roof snow mass, $L_{\max}$ (kg m$^{-1}$)",
        ylabel=r"Maximum one-step shed mass, $S_{\max}$ (kg m$^{-1}$)",
    )
    axis.legend(frameon=False)
    _save_figure(figure, root, "figure_3_primary_pareto_comparison")

    figure, axis = plt.subplots(figsize=(6.5, 5.0))
    for label, frame, color in [
        ("geometry only", geometry, "#2ca02c"),
        ("surface only", surface, "#ff7f0e"),
        ("joint", joint, "#9467bd"),
        ("uniform", uniform, "#7f7f7f"),
    ]:
        axis.scatter(
            frame["l_max_kg_per_m"],
            frame["s_max_kg_per_m"],
            s=12,
            alpha=0.55,
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
    figure, axes = plt.subplots(1, 2, figsize=(9.0, 3.8), sharey=True)
    for axis, objective, title in [
        (axes[0], "l_max_kg_per_m_relative_error", r"$L_{\max}$"),
        (axes[1], "s_max_kg_per_m_relative_error", r"$S_{\max}$"),
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
        axis.set(xlabel="Time step (h)", title=title)
    axes[0].set_ylabel("Relative error versus 48-cell, 0.5-h reference")
    axes[1].legend(frameon=False)
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
    high = sensitivity.loc[sensitivity["level"] == "high"].sort_values(
        "relative_l_change"
    )
    figure, axis = plt.subplots(figsize=(7.5, 6.0))
    y = np.arange(len(high))
    axis.barh(
        y - 0.18,
        high["relative_l_change"],
        height=0.35,
        label=r"$L_{\max}$",
    )
    axis.barh(
        y + 0.18,
        high["relative_s_change"],
        height=0.35,
        label=r"$S_{\max}$",
    )
    axis.set(
        yticks=y,
        yticklabels=high["dimension"],
        xlabel="Relative change under high perturbation",
    )
    axis.axvline(0.0, color="black", linewidth=0.8)
    axis.legend(frameon=False)
    _save_figure(figure, root, "figure_7_sensitivity")

    robustness = pd.read_csv(results / "robustness.csv")
    figure, axis = plt.subplots(figsize=(6.5, 5.0))
    for design_class, group in robustness.groupby("design_class"):
        axis.scatter(
            group["l_max_kg_per_m"],
            group["s_max_kg_per_m"],
            s=12,
            alpha=0.35,
            label=design_class,
        )
    axis.set(
        xlabel=r"Perturbed $L_{\max}$ (kg m$^{-1}$)",
        ylabel=r"Perturbed $S_{\max}$ (kg m$^{-1}$)",
    )
    axis.legend(frameon=False)
    _save_figure(figure, root, "figure_8_monte_carlo_robustness")

    labor = pd.read_csv(tables / "table_5_labor_scarcity.csv")
    labor = labor.loc[labor["labor_scarcity"].isin(["low", "medium", "high"])]
    phase = pd.read_csv(tables / "table_4_strategy_phase_diagram.csv")
    figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.3))
    axes[0].plot(
        labor["l_max_kg_per_m"],
        labor["s_max_kg_per_m"],
        marker="o",
    )
    for _, row in labor.iterrows():
        axes[0].annotate(
            row["labor_scarcity"],
            (row["l_max_kg_per_m"], row["s_max_kg_per_m"]),
            xytext=(5, 5),
            textcoords="offset points",
        )
    axes[0].set(
        xlabel=r"Selected $L_{\max}$ (kg m$^{-1}$)",
        ylabel=r"Selected $S_{\max}$ (kg m$^{-1}$)",
        title="Labor-scarcity choices",
    )
    colors = {
        "RETENTION": "#1f77b4",
        "UNIFORM_INTERMEDIATE": "#7f7f7f",
        "SHEDDING": "#d62728",
        "GRADED_HYBRID": "#9467bd",
    }
    for strategy, group in phase.groupby("strategy"):
        axes[1].scatter(
            group["l_max_kg_per_m"],
            group["s_max_kg_per_m"],
            s=14,
            alpha=0.65,
            color=colors[strategy],
            label=strategy.replace("_", " ").title(),
        )
    axes[1].set(
        xlabel=r"$L_{\max}$ (kg m$^{-1}$)",
        ylabel=r"$S_{\max}$ (kg m$^{-1}$)",
        title="Strategy classification",
    )
    axes[1].legend(frameon=False, fontsize=7)
    _save_figure(figure, root, "figure_9_decision_phase_diagram")
