from __future__ import annotations

from dataclasses import asdict

import numpy as np

from graded_roof.metrics import total_variation, transition_count
from graded_roof.models import RoofDesign, SimulationConfig, SimulationResult, WeatherSeries
from graded_roof.simulation import simulate
from graded_roof.weather import synthetic_weather


def simulation_config(config: dict) -> SimulationConfig:
    snow = config["snow"]
    simulation = config["simulation"]
    return SimulationConfig(
        gravity_m_s2=snow["gravity_m_s2"],
        melt_factor_kg_m2_c_h=snow["melt_factor_kg_m2_c_h"],
        rain_heat_factor_kg_m2_mm=snow["rain_heat_factor_kg_m2_mm"],
        initial_density_kg_m3=snow["initial_density_kg_m3"],
        maximum_density_kg_m3=snow["maximum_density_kg_m3"],
        compaction_rate_per_day=snow["compaction_rate_per_day"],
        dynamic_friction_age_scale_days=snow[
            "dynamic_friction_age_scale_days"
        ],
        friction_age_gain=snow["friction_age_gain"],
        near_melt_friction_loss=snow["near_melt_friction_loss"],
        near_melt_center_c=snow["near_melt_center_c"],
        near_melt_width_c=snow["near_melt_width_c"],
        friction_model=simulation["friction_model"],
        transport_fraction_limit=simulation["transport_fraction_limit"],
        event_threshold_kg_per_m=simulation["event_threshold_kg_per_m"],
        intervention_mass_kg_per_m=snow["intervention_mass_kg_per_m"],
    )


def synthetic_weather_set(config: dict) -> list[WeatherSeries]:
    settings = config["synthetic_weather"]
    dt_hours = config["simulation"]["dt_hours"]
    return [
        synthetic_weather(
            **scenario,
            duration_h=settings["duration_h"],
            dt_hours=dt_hours,
        )
        for scenario in settings["scenarios"]
    ]


def interpolate_profile(control_points: np.ndarray, cells: int) -> np.ndarray:
    values = np.asarray(control_points, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("control_points must be a one-dimensional array")
    return np.interp(
        np.linspace(0.0, 1.0, cells),
        np.linspace(0.0, 1.0, values.size),
        values,
    )


def heterogeneous_design(
    variables: np.ndarray,
    config: dict,
    mode: str,
    *,
    label: str,
) -> RoofDesign:
    cells = config["roof"]["cells"]
    control_points = config["optimizer"]["profile_control_points"]
    variables = np.asarray(variables, dtype=float)
    uniform_reference = config["baselines"]["uniform_intermediate"]
    fixed_slope = uniform_reference["slope_deg"]
    fixed_mu = uniform_reference["mu_static"]
    fixed_adhesion = uniform_reference["adhesion_pa"]
    if mode == "geometry":
        slope_controls = variables
        mu_controls = np.full(control_points, fixed_mu)
        adhesion_controls = np.full(control_points, fixed_adhesion)
    elif mode == "surface":
        slope_controls = np.full(control_points, fixed_slope)
        mu_controls = variables[:control_points]
        adhesion_controls = variables[control_points:]
    elif mode == "joint":
        slope_controls = variables[:control_points]
        mu_controls = variables[control_points : 2 * control_points]
        adhesion_controls = variables[2 * control_points :]
    else:
        raise ValueError("mode must be geometry, surface, or joint")
    mu_static = interpolate_profile(mu_controls, cells)
    return RoofDesign(
        slope_deg=interpolate_profile(slope_controls, cells),
        mu_static=mu_static,
        mu_kinetic=mu_static * config["surface"]["kinetic_ratio"],
        adhesion_pa=interpolate_profile(adhesion_controls, cells),
        length_m=config["roof"]["length_m"],
        width_m=config["roof"]["width_m"],
        label=label,
    )


def uniform_design(
    config: dict,
    slope_deg: float,
    mu_static: float,
    adhesion_pa: float,
    *,
    label: str,
) -> RoofDesign:
    return RoofDesign.uniform(
        cells=config["roof"]["cells"],
        length_m=config["roof"]["length_m"],
        slope_deg=slope_deg,
        mu_static=mu_static,
        mu_kinetic=mu_static * config["surface"]["kinetic_ratio"],
        adhesion_pa=adhesion_pa,
        label=label,
    )


def result_record(result: SimulationResult) -> dict[str, float | int]:
    excluded = {
        "roof_mass_kg_per_m",
        "pre_release_roof_mass_kg_per_m",
        "pre_release_max_depth_m",
        "shed_mass_kg_per_m",
        "melt_mass_kg_per_m",
        "density_kg_m3",
        "final_cell_mass_kg_per_m",
    }
    return {
        key: value
        for key, value in asdict(result).items()
        if key not in excluded
    }


def evaluate_design(
    design: RoofDesign,
    weathers: list[WeatherSeries],
    simulation_settings: SimulationConfig,
) -> tuple[dict[str, float | int | str], list[dict[str, float | int | str]]]:
    scenario_records: list[dict[str, float | int | str]] = []
    for weather in weathers:
        result = simulate(design, weather, simulation_settings)
        scenario_records.append(
            {
                "design": design.label,
                "weather": weather.name,
                **result_record(result),
            }
        )
    aggregate: dict[str, float | int | str] = {
        "design": design.label,
        "l_max_kg_per_m": max(
            float(record["l_max_kg_per_m"]) for record in scenario_records
        ),
        "s_max_kg_per_m": max(
            float(record["s_max_kg_per_m"]) for record in scenario_records
        ),
        "mean_ssci": float(
            np.mean([float(record["ssci"]) for record in scenario_records])
        ),
        "mean_input_snow_kg_per_m": float(
            np.mean(
                [float(record["input_snow_kg_per_m"]) for record in scenario_records]
            )
        ),
        "mean_total_shed_kg_per_m": float(
            np.mean(
                [
                    float(record["total_shed_kg_per_m"])
                    for record in scenario_records
                ]
            )
        ),
        "mean_event_count": float(
            np.mean(
                [float(record["shed_event_count"]) for record in scenario_records]
            )
        ),
        "mean_event_mass_kg_per_m": float(
            np.mean(
                [
                    float(record["mean_shed_event_mass_kg_per_m"])
                    for record in scenario_records
                ]
            )
        ),
        "median_event_mass_kg_per_m": float(
            np.mean(
                [
                    float(record["median_shed_event_mass_kg_per_m"])
                    for record in scenario_records
                ]
            )
        ),
        "mean_kinetic_energy_proxy_j_per_m": float(
            np.mean(
                [
                    float(record["kinetic_energy_proxy_j_per_m"])
                    for record in scenario_records
                ]
            )
        ),
        "mean_time_above_intervention_h": float(
            np.mean(
                [
                    float(record["time_above_intervention_h"])
                    for record in scenario_records
                ]
            )
        ),
        "mean_manual_triggers": float(
            np.mean(
                [float(record["manual_triggers"]) for record in scenario_records]
            )
        ),
        "mean_residual_mass_kg_per_m": float(
            np.mean(
                [
                    float(record["residual_mass_kg_per_m"])
                    for record in scenario_records
                ]
            )
        ),
        "maximum_snow_depth_m": max(
            float(record["maximum_snow_depth_m"]) for record in scenario_records
        ),
        "max_abs_mass_balance_error_kg_per_m": max(
            abs(float(record["mass_balance_error_kg_per_m"]))
            for record in scenario_records
        ),
        "slope_total_variation_deg": total_variation(design.slope_deg),
        "surface_total_variation": total_variation(design.mu_static),
        "slope_transition_count": transition_count(design.slope_deg),
        "surface_transition_count": transition_count(design.mu_static),
    }
    return aggregate, scenario_records
