from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from graded_roof.audits import generate_audits, generate_initial_audits
from graded_roof.complexity import design_complexity
from graded_roof.config import load_config
from graded_roof.jma import daily_weather, parse_daily_html
from graded_roof.manuscript import (
    build_cover_letter,
    build_editable_figures,
    build_editable_tables,
    build_inline_manuscript,
    build_manuscript,
    build_supplement,
    build_text_files,
    package_submission,
    write_manifest,
)
from graded_roof.metrics import (
    additive_epsilon_indicator,
    nondominated_mask,
    normalized_hypervolume_2d,
)
from graded_roof.optimization import combine_fronts, run_optimization
from graded_roof.reporting import generate_figures, generate_tables
from graded_roof.study import (
    evaluate_design,
    heterogeneous_design,
    simulation_config,
    synthetic_weather_set,
    uniform_design,
)
from graded_roof.validation import validate_submission, write_validation_report
from graded_roof.weather import resample_weather

ROOT = Path(__file__).resolve().parents[1]


def write_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def select_knee(front: pd.DataFrame) -> pd.Series:
    objectives = front[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy()
    span = np.ptp(objectives, axis=0)
    normalized = (objectives - objectives.min(axis=0)) / np.where(
        span > 0,
        span,
        1.0,
    )
    return front.iloc[int(np.argmin(np.linalg.norm(normalized, axis=1)))]


def design_from_front_row(row: pd.Series, config: dict, mode: str):
    variable_columns = sorted(
        [column for column in row.index if column.startswith("x_")],
        key=lambda column: int(column.split("_", maxsplit=1)[1]),
    )
    return heterogeneous_design(
        row[variable_columns].to_numpy(dtype=float),
        config,
        mode,
        label=f"{mode}_knee",
    )


def stage_data(config: dict) -> None:
    output = ROOT / "data" / "processed" / "synthetic"
    output.mkdir(parents=True, exist_ok=True)
    for weather in synthetic_weather_set(config):
        frame = pd.DataFrame(
            {
                "time_h": np.arange(len(weather.temperature_c)) * weather.dt_hours,
                "temperature_c": weather.temperature_c,
                "snowfall_kg_m2": weather.snowfall_kg_m2,
                "rain_mm": weather.rain_mm,
            }
        )
        write_frame(frame, output / f"{weather.name}.csv")
    manifest = {
        "source": "deterministic synthetic scenarios defined in config/production.yaml",
        "scenario_count": len(config["synthetic_weather"]["scenarios"]),
        "dt_hours": config["simulation"]["dt_hours"],
        "seed": config["project"]["seed"],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def stage_baseline(config: dict) -> None:
    weathers = synthetic_weather_set(config)
    settings = simulation_config(config)
    designs = [
        uniform_design(
            config,
            parameters["slope_deg"],
            parameters["mu_static"],
            parameters["adhesion_pa"],
            label=label,
        )
        for label, parameters in config["baselines"].items()
    ]
    aggregate_rows: list[dict] = []
    scenario_rows: list[dict] = []
    for design in designs:
        aggregate, scenarios = evaluate_design(design, weathers, settings)
        aggregate_rows.append(aggregate)
        scenario_rows.extend(scenarios)
    results = ROOT / config["project"]["results_dir"]
    write_frame(pd.DataFrame(aggregate_rows), results / "baseline_aggregate.csv")
    write_frame(pd.DataFrame(scenario_rows), results / "baseline_scenarios.csv")


def stage_convergence(config: dict) -> None:
    settings = simulation_config(config)
    master_config = json.loads(json.dumps(config))
    master_config["simulation"]["dt_hours"] = min(config["convergence"]["dt_hours"])
    master_weathers = synthetic_weather_set(master_config)
    rows: list[dict] = []
    for cells in config["convergence"]["cells"]:
        design_config = json.loads(json.dumps(config))
        design_config["roof"]["cells"] = cells
        parameters = config["baselines"]["uniform_intermediate"]
        design = uniform_design(
            design_config,
            parameters["slope_deg"],
            parameters["mu_static"],
            parameters["adhesion_pa"],
            label=f"convergence_{cells}",
        )
        for dt_hours in config["convergence"]["dt_hours"]:
            weathers = [
                resample_weather(weather, dt_hours) for weather in master_weathers
            ]
            aggregate, _ = evaluate_design(design, weathers, settings)
            rows.append(
                {
                    "cells": cells,
                    "dt_hours": dt_hours,
                    **aggregate,
                }
            )
    frame = pd.DataFrame(rows)
    reference = frame.loc[
        (frame["cells"] == max(config["convergence"]["cells"]))
        & (frame["dt_hours"] == min(config["convergence"]["dt_hours"]))
    ].iloc[0]
    convergence_metrics = [
        "l_max_kg_per_m",
        "s_max_kg_per_m",
        "mean_event_count",
        "mean_ssci",
    ]
    for objective in convergence_metrics:
        denominator = max(abs(float(reference[objective])), 1e-12)
        frame[f"{objective}_relative_error"] = (
            (frame[objective] - float(reference[objective])).abs() / denominator
        )
    frame["within_tolerance"] = (
        frame[
            [f"{metric}_relative_error" for metric in convergence_metrics]
        ].max(axis=1)
        <= config["convergence"]["relative_tolerance"]
    )
    results = ROOT / config["project"]["results_dir"]
    write_frame(frame, results / "convergence.csv")


def stage_uniform(config: dict) -> None:
    weathers = synthetic_weather_set(config)
    settings = simulation_config(config)
    grid_size = config["optimizer"]["uniform_slope_grid"]
    slopes = np.linspace(*config["roof"]["slope_bounds_deg"], grid_size)
    frictions = np.linspace(
        *config["surface"]["static_friction_bounds"],
        config["optimizer"]["uniform_friction_grid"],
    )
    adhesion_levels = np.linspace(
        *config["surface"]["adhesion_bounds_pa"],
        config["optimizer"]["uniform_adhesion_grid"],
    )
    rows: list[dict] = []
    for slope_index, slope in enumerate(slopes):
        for friction_index, friction in enumerate(frictions):
            for adhesion_index, adhesion in enumerate(adhesion_levels):
                design = uniform_design(
                    config,
                    float(slope),
                    float(friction),
                    float(adhesion),
                    label=(
                        f"uniform_{slope_index:02d}_{friction_index:02d}_"
                        f"{adhesion_index:02d}"
                    ),
                )
                aggregate, _ = evaluate_design(design, weathers, settings)
                rows.append(
                    {
                        "slope_deg": slope,
                        "mu_static": friction,
                        "mu_kinetic": friction
                        * config["surface"]["kinetic_ratio"],
                        "adhesion_pa": adhesion,
                        **aggregate,
                    }
                )
    frame = pd.DataFrame(rows)
    mask = nondominated_mask(
        frame[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy()
    )
    results = ROOT / config["project"]["results_dir"]
    write_frame(frame, results / "uniform_design_space.csv")
    write_frame(
        frame.loc[mask].sort_values(["l_max_kg_per_m", "s_max_kg_per_m"]),
        results / "uniform_pareto.csv",
    )


def stage_optimize(config: dict) -> None:
    weathers = synthetic_weather_set(config)
    settings = simulation_config(config)
    results = ROOT / config["project"]["results_dir"]
    dt_token = str(config["simulation"]["dt_hours"]).replace(".", "p")
    checkpoints = ROOT / "checkpoints" / f"dt_{dt_token}h"
    jobs = [
        (mode, seed)
        for mode in ["geometry", "surface", "joint"]
        for seed in config["optimizer"]["seeds"]
    ]
    completed_paths: dict[tuple[str, int], Path] = {}
    workers = min(
        int(config["optimizer"].get("parallel_workers", 1)),
        len(jobs),
    )
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=workers
    ) as executor:
        futures = {
            executor.submit(
                run_optimization,
                config,
                weathers,
                settings,
                mode,
                seed,
                results_dir=results,
                checkpoint_dir=checkpoints,
            ): (mode, seed)
            for mode, seed in jobs
        }
        for future in concurrent.futures.as_completed(futures):
            mode, seed = futures[future]
            completed_paths[(mode, seed)] = future.result()

    stochasticity_rows = []
    for mode in ["geometry", "surface", "joint"]:
        paths = [
            completed_paths[(mode, seed)]
            for seed in config["optimizer"]["seeds"]
        ]
        output_path = results / f"{mode}_pareto.csv"
        front = combine_fronts(paths, output_path)
        enriched_rows = []
        for _, row in front.iterrows():
            design = design_from_front_row(row, config, mode)
            aggregate, _ = evaluate_design(design, weathers, settings)
            enriched_rows.append({**row.to_dict(), **aggregate})
        write_frame(pd.DataFrame(enriched_rows), output_path)
        objective_columns = ["l_max_kg_per_m", "s_max_kg_per_m"]
        combined_objectives = front[objective_columns].to_numpy()
        objective_minimum = combined_objectives.min(axis=0)
        objective_span = np.ptp(combined_objectives, axis=0)
        normalized_combined = (
            combined_objectives - objective_minimum
        ) / np.where(objective_span > 0, objective_span, 1.0)
        reference = tuple(combined_objectives.max(axis=0) * 1.05)
        for seed, path in zip(config["optimizer"]["seeds"], paths, strict=True):
            seed_front = pd.read_csv(path)
            seed_objectives = seed_front[objective_columns].to_numpy()
            normalized_seed = (
                seed_objectives - objective_minimum
            ) / np.where(objective_span > 0, objective_span, 1.0)
            stochasticity_rows.append(
                {
                    "design_class": mode,
                    "seed": seed,
                    "pareto_designs": len(seed_front),
                    "minimum_l_max_kg_per_m": seed_objectives[:, 0].min(),
                    "minimum_s_max_kg_per_m": seed_objectives[:, 1].min(),
                    "normalized_hypervolume": normalized_hypervolume_2d(
                        seed_objectives,
                        reference,
                    ),
                    "additive_epsilon_vs_combined": additive_epsilon_indicator(
                        normalized_seed,
                        normalized_combined,
                    ),
                }
            )
    write_frame(
        pd.DataFrame(stochasticity_rows),
        results / "optimizer_stochasticity.csv",
    )


def stage_jma(config: dict) -> None:
    snapshots = sorted((ROOT / "data" / "raw" / "jma_daily").glob("*"))
    if not snapshots:
        raise FileNotFoundError("no persistent JMA daily snapshot is available")
    snapshot = snapshots[-1]
    frames = []
    for path in sorted(snapshot.glob("*_daily.html")):
        station_id, year, month, _ = path.stem.split("_")
        frames.append(
            parse_daily_html(path, station_id, int(year), int(month))
        )
    observations = pd.concat(frames, ignore_index=True).sort_values(
        ["station_id", "date"]
    )
    observations["winter"] = np.where(
        observations["date"].dt.month >= config["jma"]["season_start_month"],
        observations["date"].dt.year,
        observations["date"].dt.year - 1,
    )
    write_frame(
        observations,
        ROOT / "data" / "processed" / "jma_daily_observations.csv",
    )
    results = ROOT / config["project"]["results_dir"]
    uniform_row = select_knee(pd.read_csv(results / "uniform_pareto.csv"))
    designs = [
        uniform_design(
            config,
            float(uniform_row["slope_deg"]),
            float(uniform_row["mu_static"]),
            float(uniform_row["adhesion_pa"]),
            label="uniform_knee",
        ),
        design_from_front_row(
            select_knee(pd.read_csv(results / "joint_pareto.csv")),
            config,
            "joint",
        ),
    ]
    settings = simulation_config(config)
    rows = []
    for (station_id, winter), group in observations.groupby(
        ["station_id", "winter"]
    ):
        if int(winter) not in config["jma"]["winters"]:
            continue
        weather = daily_weather(
            group,
            fresh_snow_density_kg_m3=settings.initial_density_kg_m3,
            name=f"{station_id}_winter_{winter}_{int(winter) + 1}",
        )
        for design in designs:
            aggregate, scenarios = evaluate_design(design, [weather], settings)
            rows.append(
                {
                    "station_id": station_id,
                    "winter": int(winter),
                    "days": len(group),
                    "missing_temperature_days": int(
                        group["mean_temperature_c"].isna().sum()
                    ),
                    "missing_snowfall_days": int(
                        group["snowfall_depth_cm"].isna().sum()
                    ),
                    "design_class": design.label,
                    **aggregate,
                    "source_scenario": scenarios[0]["weather"],
                }
            )
    write_frame(pd.DataFrame(rows), results / "jma_daily_evaluation.csv")


def perturb_weather(weathers, dimension: str, factor: float):
    perturbed = []
    for weather in weathers:
        if dimension == "temperature":
            temperature = weather.temperature_c + factor
            snowfall = weather.snowfall_kg_m2
            rain = weather.rain_mm
        elif dimension == "snowfall":
            temperature = weather.temperature_c
            snowfall = weather.snowfall_kg_m2 * factor
            rain = weather.rain_mm
        elif dimension == "rain_on_snow":
            temperature = weather.temperature_c
            snowfall = weather.snowfall_kg_m2
            rain = weather.rain_mm * factor
        else:
            perturbed.append(weather)
            continue
        perturbed.append(
            replace(
                weather,
                temperature_c=temperature,
                snowfall_kg_m2=snowfall,
                rain_mm=rain,
                name=f"{weather.name}_{dimension}",
            )
        )
    return perturbed


def stage_sensitivity(config: dict) -> None:
    results = ROOT / config["project"]["results_dir"]
    front = pd.read_csv(results / "joint_pareto.csv")
    design = design_from_front_row(select_knee(front), config, "joint")
    base_weathers = synthetic_weather_set(config)
    base_settings = simulation_config(config)
    base, _ = evaluate_design(design, base_weathers, base_settings)
    rows: list[dict] = []
    relative = config["sensitivity"]["relative_perturbation"]
    for dimension in config["sensitivity"]["dimensions"]:
        for level, factor in [("low", 1.0 - relative), ("high", 1.0 + relative)]:
            candidate = design
            settings = base_settings
            weathers = base_weathers
            recorded_factor = factor
            if dimension == "static_friction":
                candidate = replace(
                    design,
                    mu_static=design.mu_static * factor,
                )
            elif dimension == "kinetic_friction":
                candidate = replace(
                    design,
                    mu_kinetic=design.mu_kinetic * factor,
                )
            elif dimension == "adhesion":
                candidate = replace(
                    design,
                    adhesion_pa=design.adhesion_pa * factor,
                )
            elif dimension == "fresh_snow_density":
                settings = replace(
                    settings,
                    initial_density_kg_m3=settings.initial_density_kg_m3 * factor,
                )
            elif dimension == "aging_rate":
                settings = replace(
                    settings,
                    dynamic_friction_age_scale_days=(
                        settings.dynamic_friction_age_scale_days / factor
                    ),
                )
            elif dimension == "temperature":
                weathers = perturb_weather(
                    base_weathers,
                    dimension,
                    -1.5 if level == "low" else 1.5,
                )
            elif dimension == "snowfall":
                weathers = perturb_weather(base_weathers, dimension, factor)
            elif dimension == "roof_length":
                candidate = replace(design, length_m=design.length_m * factor)
            elif dimension == "cells":
                cells = 12 if level == "low" else 48
                candidate = replace(
                    design,
                    slope_deg=np.interp(
                        np.linspace(0, 1, cells),
                        np.linspace(0, 1, design.cells),
                        design.slope_deg,
                    ),
                    mu_static=np.interp(
                        np.linspace(0, 1, cells),
                        np.linspace(0, 1, design.cells),
                        design.mu_static,
                    ),
                    mu_kinetic=np.interp(
                        np.linspace(0, 1, cells),
                        np.linspace(0, 1, design.cells),
                        design.mu_kinetic,
                    ),
                    adhesion_pa=np.interp(
                        np.linspace(0, 1, cells),
                        np.linspace(0, 1, design.cells),
                        design.adhesion_pa,
                    ),
                )
            elif dimension == "dt":
                weathers = [
                    resample_weather(weather, 2.0 if level == "low" else 0.5)
                    if not np.isclose(
                        weather.dt_hours,
                        2.0 if level == "low" else 0.5,
                    )
                    else weather
                    for weather in (
                        synthetic_weather_set(
                            {
                                **config,
                                "simulation": {
                                    **config["simulation"],
                                    "dt_hours": 0.5,
                                },
                            }
                        )
                    )
                ]
            elif dimension == "slope_limits":
                candidate = replace(
                    design,
                    slope_deg=np.clip(
                        design.slope_deg * factor,
                        config["roof"]["slope_bounds_deg"][0],
                        config["roof"]["slope_bounds_deg"][1],
                    ),
                )
            elif dimension == "adjacent_slope_limit":
                slope = design.slope_deg.copy()
                adjacent_limit = (
                    config["roof"]["adjacent_slope_limit_deg"] * factor
                )
                for index in range(1, len(slope)):
                    slope[index] = np.clip(
                        slope[index],
                        slope[index - 1] - adjacent_limit,
                        slope[index - 1] + adjacent_limit,
                    )
                for index in range(len(slope) - 2, -1, -1):
                    slope[index] = np.clip(
                        slope[index],
                        slope[index + 1] - adjacent_limit,
                        slope[index + 1] + adjacent_limit,
                    )
                candidate = replace(
                    design,
                    slope_deg=slope,
                )
            elif dimension == "transition_penalty":
                penalty = (
                    0.0
                    if level == "low"
                    else config["complexity"]["transition_penalty_high"]
                )
                objective_values = front[
                    ["l_max_kg_per_m", "s_max_kg_per_m"]
                ]
                objective_span = objective_values.max() - objective_values.min()
                normalized = (
                    objective_values - objective_values.min()
                ) / objective_span.replace(0, 1)
                transition_fraction = []
                for _, front_row in front.iterrows():
                    front_design = design_from_front_row(front_row, config, "joint")
                    complexity = design_complexity(
                        front_design,
                        config["surface"]["discrete_classes"],
                        slope_rounding_deg=config["complexity"][
                            "slope_rounding_deg"
                        ],
                    )
                    transition_fraction.append(
                        complexity["transition_count"]
                        / max(config["roof"]["maximum_transitions"], 1)
                    )
                score = (
                    normalized["l_max_kg_per_m"]
                    + normalized["s_max_kg_per_m"]
                    + penalty * np.asarray(transition_fraction)
                )
                candidate = design_from_front_row(
                    front.loc[score.idxmin()],
                    config,
                    "joint",
                )
                recorded_factor = penalty
            elif dimension == "rain_on_snow":
                weathers = perturb_weather(base_weathers, dimension, factor)
            elif dimension == "friction_model":
                settings = replace(
                    settings,
                    friction_model="constant" if level == "low" else "dynamic",
                )
            aggregate, _ = evaluate_design(candidate, weathers, settings)
            rows.append(
                {
                    "dimension": dimension,
                    "level": level,
                    "factor": recorded_factor,
                    "baseline_l_max_kg_per_m": base["l_max_kg_per_m"],
                    "baseline_s_max_kg_per_m": base["s_max_kg_per_m"],
                    **aggregate,
                }
            )
    write_frame(pd.DataFrame(rows), results / "sensitivity.csv")


def stage_robustness(config: dict) -> None:
    results = ROOT / config["project"]["results_dir"]
    candidate_count = config["robustness"]["candidate_count_per_class"]
    candidates = []
    for design_class in ["uniform", "joint"]:
        front = pd.read_csv(results / f"{design_class}_pareto.csv").sort_values(
            "l_max_kg_per_m"
        )
        objective_values = front[
            ["l_max_kg_per_m", "s_max_kg_per_m"]
        ].to_numpy()
        objective_span = np.ptp(objective_values, axis=0)
        normalized = (
            objective_values - objective_values.min(axis=0)
        ) / np.where(objective_span > 0, objective_span, 1.0)
        knee_index = int(np.argmin(np.linalg.norm(normalized, axis=1)))
        spaced_indices = np.linspace(
            0,
            len(front) - 1,
            min(candidate_count, len(front)),
            dtype=int,
        )
        selected_indices = np.unique(np.append(spaced_indices, knee_index))
        for candidate_index, row_index in enumerate(selected_indices):
            row = front.iloc[int(row_index)]
            candidate_id = f"{design_class}_{candidate_index:02d}"
            if design_class == "uniform":
                design = uniform_design(
                    config,
                    float(row["slope_deg"]),
                    float(row["mu_static"]),
                    float(row["adhesion_pa"]),
                    label=candidate_id,
                )
            else:
                design = replace(
                    design_from_front_row(row, config, "joint"),
                    label=candidate_id,
                )
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "design_class": design_class,
                    "nominal_knee": int(row_index) == knee_index,
                    "design": design,
                    "nominal_l_max_kg_per_m": float(row["l_max_kg_per_m"]),
                    "nominal_s_max_kg_per_m": float(row["s_max_kg_per_m"]),
                }
            )
    base_weathers = synthetic_weather_set(config)
    base_settings = simulation_config(config)
    coefficient = config["robustness"]["coefficient_of_variation"]
    rng = np.random.default_rng(config["robustness"]["seed"])
    rows: list[dict] = []
    for sample in range(config["robustness"]["samples"]):
        friction_factor = max(0.05, rng.normal(1.0, coefficient["friction"]))
        adhesion_factor = max(0.0, rng.normal(1.0, coefficient["adhesion"]))
        density_factor = max(
            0.05,
            rng.normal(1.0, coefficient["fresh_snow_density"]),
        )
        snowfall_factor = max(0.0, rng.normal(1.0, coefficient["snowfall"]))
        temperature_shift = rng.normal(0.0, coefficient["temperature_sd_c"])
        weathers = []
        for weather in base_weathers:
            weathers.append(
                replace(
                    weather,
                    temperature_c=weather.temperature_c + temperature_shift,
                    snowfall_kg_m2=weather.snowfall_kg_m2 * snowfall_factor,
                    name=f"{weather.name}_mc_{sample}",
                )
            )
        settings = replace(
            base_settings,
            initial_density_kg_m3=(
                base_settings.initial_density_kg_m3 * density_factor
            ),
        )
        for candidate_details in candidates:
            design = candidate_details["design"]
            candidate = replace(
                design,
                mu_static=design.mu_static * friction_factor,
                mu_kinetic=design.mu_kinetic * friction_factor,
                adhesion_pa=design.adhesion_pa * adhesion_factor,
            )
            aggregate, _ = evaluate_design(candidate, weathers, settings)
            rows.append(
                {
                    "sample": sample,
                    "candidate_id": candidate_details["candidate_id"],
                    "design_class": candidate_details["design_class"],
                    "nominal_knee": candidate_details["nominal_knee"],
                    "nominal_l_max_kg_per_m": candidate_details[
                        "nominal_l_max_kg_per_m"
                    ],
                    "nominal_s_max_kg_per_m": candidate_details[
                        "nominal_s_max_kg_per_m"
                    ],
                    "friction_factor": friction_factor,
                    "adhesion_factor": adhesion_factor,
                    "density_factor": density_factor,
                    "snowfall_factor": snowfall_factor,
                    "temperature_shift_c": temperature_shift,
                    **aggregate,
                }
            )
    robustness = pd.DataFrame(rows)
    write_frame(robustness, results / "robustness.csv")
    quantile = config["robustness"]["robust_quantile"]
    summary_rows = []
    for (candidate_id, design_class), group in robustness.groupby(
        ["candidate_id", "design_class"]
    ):
        summary_rows.append(
            {
                "candidate_id": candidate_id,
                "design_class": design_class,
                "nominal_knee": bool(group["nominal_knee"].iloc[0]),
                "nominal_l_max_kg_per_m": group[
                    "nominal_l_max_kg_per_m"
                ].iloc[0],
                "nominal_s_max_kg_per_m": group[
                    "nominal_s_max_kg_per_m"
                ].iloc[0],
                "mean_l_max_kg_per_m": group["l_max_kg_per_m"].mean(),
                "quantile_l_max_kg_per_m": group["l_max_kg_per_m"].quantile(
                    quantile
                ),
                "mean_s_max_kg_per_m": group["s_max_kg_per_m"].mean(),
                "quantile_s_max_kg_per_m": group["s_max_kg_per_m"].quantile(
                    quantile
                ),
                "mean_ssci": group["mean_ssci"].mean(),
                "quantile_ssci": group["mean_ssci"].quantile(quantile),
                "mean_maximum_snow_depth_m": group[
                    "maximum_snow_depth_m"
                ].mean(),
                "quantile_maximum_snow_depth_m": group[
                    "maximum_snow_depth_m"
                ].quantile(quantile),
                "mean_manual_triggers": group["mean_manual_triggers"].mean(),
                "probability_manual_intervention": float(
                    (group["mean_manual_triggers"] > 0).mean()
                ),
            }
        )
    summary = pd.DataFrame(summary_rows)
    robust_objectives = summary[
        [
            "quantile_l_max_kg_per_m",
            "quantile_s_max_kg_per_m",
            "probability_manual_intervention",
        ]
    ]
    robust_span = robust_objectives.max() - robust_objectives.min()
    normalized = (
        robust_objectives - robust_objectives.min()
    ) / robust_span.replace(0, 1)
    summary["robust_selection_score"] = normalized.sum(axis=1)
    summary["robust_selected"] = False
    summary.loc[summary["robust_selection_score"].idxmin(), "robust_selected"] = True
    write_frame(summary, results / "robustness_summary.csv")


def stage_tables(config: dict) -> None:
    generate_tables(config, ROOT)


def stage_figures(config: dict) -> None:
    generate_figures(config, ROOT)


def stage_manuscript(config: dict) -> None:
    del config
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_acquisition_ledger.py")],
        cwd=ROOT,
        check=True,
    )
    artifacts = [
        *generate_initial_audits(ROOT),
        build_manuscript(ROOT),
        build_inline_manuscript(ROOT),
        build_editable_tables(ROOT),
        build_editable_figures(ROOT),
        build_supplement(ROOT),
        build_cover_letter(ROOT),
        *build_text_files(ROOT),
    ]
    artifacts.append(write_manifest(ROOT, artifacts))
    package_submission(ROOT)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "update_project_state.py")],
        cwd=ROOT,
        check=True,
    )


def stage_validate(config: dict) -> None:
    del config
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "hard_code_audit.py")],
        cwd=ROOT,
        check=True,
    )
    package_submission(ROOT)
    report = validate_submission(ROOT)
    write_validation_report(ROOT, report)
    generate_audits(ROOT, report)
    package_submission(ROOT)
    report = validate_submission(ROOT)
    write_validation_report(ROOT, report)
    generate_audits(ROOT, report)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_final_revision_fabrication.py"),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_crst_format.py"),
        ],
        cwd=ROOT,
        check=True,
    )
    build = ROOT / "manuscript" / "build"
    write_manifest(
        ROOT,
        [
            path
            for path in sorted(build.rglob("*"))
            if path.is_file() and path.name != "artifact_manifest.json"
        ],
    )
    package_submission(ROOT)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "update_project_state.py")],
        cwd=ROOT,
        check=True,
    )
    if report["errors"]:
        raise RuntimeError("\n".join(report["errors"]))


STAGES = {
    "data": stage_data,
    "baseline": stage_baseline,
    "convergence": stage_convergence,
    "uniform": stage_uniform,
    "optimize": stage_optimize,
    "jma": stage_jma,
    "sensitivity": stage_sensitivity,
    "robustness": stage_robustness,
    "tables": stage_tables,
    "figures": stage_figures,
    "manuscript": stage_manuscript,
    "validate": stage_validate,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=[*STAGES, "all"],
    )
    parser.add_argument("--config", default="config/production.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(ROOT / args.config)
    if args.stage == "all":
        for name, stage in STAGES.items():
            print(f"[pipeline] {name}", flush=True)
            stage(config)
        return
    print(f"[pipeline] {args.stage}", flush=True)
    STAGES[args.stage](config)


if __name__ == "__main__":
    main()
