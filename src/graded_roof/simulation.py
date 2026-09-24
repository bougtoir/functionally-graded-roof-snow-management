from __future__ import annotations

import numpy as np

from graded_roof.metrics import ssci
from graded_roof.models import RoofDesign, SimulationConfig, SimulationResult, WeatherSeries


def _effective_friction(
    base: np.ndarray,
    age_days: np.ndarray,
    temperature_c: float,
    config: SimulationConfig,
) -> np.ndarray:
    if config.friction_model == "constant":
        return base
    age_term = 1.0 + 0.18 * (1.0 - np.exp(-age_days / config.dynamic_friction_age_scale_days))
    near_melt_term = 1.0 - 0.22 * np.exp(-((temperature_c + 0.5) / 1.8) ** 2)
    return np.clip(base * age_term * near_melt_term, 0.01, None)


def simulate(
    design: RoofDesign,
    weather: WeatherSeries,
    config: SimulationConfig,
) -> SimulationResult:
    cells = design.cells
    area = design.cell_area_m2
    width = design.width_m
    dt_s = weather.dt_hours * 3600.0
    gravity = config.gravity_m_s2
    theta = np.deg2rad(design.slope_deg)
    mass = np.zeros(cells, dtype=float)
    age_mass_days = np.zeros(cells, dtype=float)
    density = np.full(cells, config.initial_density_kg_m3, dtype=float)
    roof_history = np.zeros(len(weather.temperature_c), dtype=float)
    shed_history = np.zeros_like(roof_history)
    melt_history = np.zeros_like(roof_history)
    energy_proxy = 0.0
    input_mass = 0.0

    for step, temperature in enumerate(weather.temperature_c):
        snowfall = weather.snowfall_kg_m2[step] * area
        mass += snowfall
        input_mass += snowfall * cells / width
        age_mass_days += mass * weather.dt_hours / 24.0

        compaction = (
            config.compaction_rate_per_day
            * weather.dt_hours
            / 24.0
            * (config.maximum_density_kg_m3 - density)
        )
        density += compaction

        potential_melt = (
            config.melt_factor_kg_m2_c_h * max(temperature, 0.0) * weather.dt_hours
            + config.rain_heat_factor_kg_m2_mm * weather.rain_mm[step]
        ) * area
        melt = np.minimum(mass, potential_melt)
        mass -= melt
        melt_history[step] = melt.sum() / width

        with np.errstate(divide="ignore", invalid="ignore"):
            age_days = np.divide(
                age_mass_days,
                mass,
                out=np.zeros_like(mass),
                where=mass > 0,
            )
        mu_static = _effective_friction(design.mu_static, age_days, temperature, config)
        mu_kinetic = _effective_friction(design.mu_kinetic, age_days, temperature, config)

        shed_step = 0.0
        for index in range(cells):
            if mass[index] <= 0:
                continue
            downslope_force = mass[index] * gravity * np.sin(theta[index])
            resistance = (
                mu_static[index] * mass[index] * gravity * np.cos(theta[index])
                + design.adhesion_pa[index] * area
            )
            if downslope_force <= resistance:
                continue
            kinetic_acceleration = gravity * (
                np.sin(theta[index]) - mu_kinetic[index] * np.cos(theta[index])
            )
            if kinetic_acceleration <= 0:
                continue
            travel_m = 0.5 * kinetic_acceleration * dt_s**2
            cell_length = design.length_m / cells
            movement_ratio = np.clip(travel_m / cell_length, 0.0, 1.0)
            fraction = min(config.transport_fraction_limit, float(movement_ratio))
            moving_mass = mass[index] * fraction
            moving_age = age_mass_days[index] * fraction
            mass[index] -= moving_mass
            age_mass_days[index] -= moving_age
            velocity = min(np.sqrt(2.0 * kinetic_acceleration * cell_length), 25.0)
            if index == cells - 1:
                shed_step += moving_mass
                energy_proxy += 0.5 * moving_mass * velocity**2 / width
            else:
                mass[index + 1] += moving_mass
                age_mass_days[index + 1] += moving_age

        shed_history[step] = shed_step / width
        roof_history[step] = mass.sum() / width

    events = shed_history[shed_history >= config.event_threshold_kg_per_m]
    final_mass = mass / width
    residual = float(final_mass.sum())
    total_melt = float(melt_history.sum())
    total_shed = float(shed_history.sum())
    balance_error = input_mass - total_melt - total_shed - residual
    above = roof_history > config.intervention_mass_kg_per_m
    manual_triggers = int(np.count_nonzero(above & ~np.r_[False, above[:-1]]))
    return SimulationResult(
        roof_mass_kg_per_m=roof_history,
        shed_mass_kg_per_m=shed_history,
        melt_mass_kg_per_m=melt_history,
        density_kg_m3=density,
        final_cell_mass_kg_per_m=final_mass,
        input_snow_kg_per_m=float(input_mass),
        l_max_kg_per_m=float(roof_history.max(initial=0.0)),
        s_max_kg_per_m=float(shed_history.max(initial=0.0)),
        ssci=ssci(events),
        total_shed_kg_per_m=total_shed,
        shed_event_count=int(events.size),
        kinetic_energy_proxy_j_per_m=float(energy_proxy),
        time_above_intervention_h=float(above.sum() * weather.dt_hours),
        manual_triggers=manual_triggers,
        residual_mass_kg_per_m=residual,
        mass_balance_error_kg_per_m=float(balance_error),
    )
