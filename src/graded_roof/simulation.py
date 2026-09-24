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
    age_term = 1.0 + config.friction_age_gain * (
        1.0 - np.exp(-age_days / config.dynamic_friction_age_scale_days)
    )
    near_melt_term = 1.0 - config.near_melt_friction_loss * np.exp(
        -(
            (temperature_c - config.near_melt_center_c)
            / config.near_melt_width_c
        )
        ** 2
    )
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
    volume = np.zeros(cells, dtype=float)
    age_mass_days = np.zeros(cells, dtype=float)
    roof_history = np.zeros(len(weather.temperature_c), dtype=float)
    pre_release_history = np.zeros_like(roof_history)
    pre_release_depth_history = np.zeros_like(roof_history)
    shed_history = np.zeros_like(roof_history)
    melt_history = np.zeros_like(roof_history)
    energy_proxy = 0.0
    input_mass = 0.0

    for step, temperature in enumerate(weather.temperature_c):
        snowfall = weather.snowfall_kg_m2[step] * area
        mass += snowfall
        volume += snowfall / config.initial_density_kg_m3
        input_mass += snowfall * cells / width
        age_mass_days += mass * weather.dt_hours / 24.0
        pre_release_history[step] = mass.sum() / width
        pre_release_depth_history[step] = np.max(volume / area, initial=0.0)

        density = np.divide(
            mass,
            volume,
            out=np.full_like(mass, config.initial_density_kg_m3),
            where=volume > 0,
        )
        density += (
            config.compaction_rate_per_day
            * weather.dt_hours
            / 24.0
            * (config.maximum_density_kg_m3 - density)
        )
        density = np.minimum(density, config.maximum_density_kg_m3)
        volume = np.divide(
            mass,
            density,
            out=np.zeros_like(mass),
            where=mass > 0,
        )

        potential_melt = (
            config.melt_factor_kg_m2_c_h * max(temperature, 0.0) * weather.dt_hours
            + config.rain_heat_factor_kg_m2_mm * weather.rain_mm[step]
        ) * area
        melt = np.minimum(mass, potential_melt)
        remaining_fraction = np.divide(
            mass - melt,
            mass,
            out=np.zeros_like(mass),
            where=mass > 0,
        )
        age_mass_days *= remaining_fraction
        volume *= remaining_fraction
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
            moving_volume = volume[index] * fraction
            mass[index] -= moving_mass
            age_mass_days[index] -= moving_age
            volume[index] -= moving_volume
            velocity = min(np.sqrt(2.0 * kinetic_acceleration * cell_length), 25.0)
            if index == cells - 1:
                shed_step += moving_mass
                energy_proxy += 0.5 * moving_mass * velocity**2 / width
            else:
                mass[index + 1] += moving_mass
                age_mass_days[index + 1] += moving_age
                volume[index + 1] += moving_volume

        shed_history[step] = shed_step / width
        roof_history[step] = mass.sum() / width

    events = shed_history[shed_history >= config.event_threshold_kg_per_m]
    final_mass = mass / width
    final_density = np.divide(
        mass,
        volume,
        out=np.full_like(mass, config.initial_density_kg_m3),
        where=volume > 0,
    )
    residual = float(final_mass.sum())
    total_melt = float(melt_history.sum())
    total_shed = float(shed_history.sum())
    balance_error = input_mass - total_melt - total_shed - residual
    above = roof_history > config.intervention_mass_kg_per_m
    manual_triggers = int(np.count_nonzero(above & ~np.r_[False, above[:-1]]))
    return SimulationResult(
        roof_mass_kg_per_m=roof_history,
        pre_release_roof_mass_kg_per_m=pre_release_history,
        pre_release_max_depth_m=pre_release_depth_history,
        shed_mass_kg_per_m=shed_history,
        melt_mass_kg_per_m=melt_history,
        density_kg_m3=final_density,
        final_cell_mass_kg_per_m=final_mass,
        input_snow_kg_per_m=float(input_mass),
        l_max_kg_per_m=float(pre_release_history.max(initial=0.0)),
        s_max_kg_per_m=float(shed_history.max(initial=0.0)),
        ssci=ssci(events),
        total_shed_kg_per_m=total_shed,
        shed_event_count=int(events.size),
        kinetic_energy_proxy_j_per_m=float(energy_proxy),
        time_above_intervention_h=float(above.sum() * weather.dt_hours),
        manual_triggers=manual_triggers,
        residual_mass_kg_per_m=residual,
        mass_balance_error_kg_per_m=float(balance_error),
        maximum_snow_depth_m=float(pre_release_depth_history.max(initial=0.0)),
    )
