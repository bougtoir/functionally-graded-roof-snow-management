from __future__ import annotations

import numpy as np

from graded_roof.models import WeatherSeries


def snowfall_depth_to_mass(
    snowfall_depth_cm: np.ndarray,
    fresh_snow_density_kg_m3: float,
) -> np.ndarray:
    if fresh_snow_density_kg_m3 <= 0:
        raise ValueError("fresh_snow_density_kg_m3 must be positive")
    depth = np.asarray(snowfall_depth_cm, dtype=float)
    if np.any(depth < 0):
        raise ValueError("snowfall depth cannot be negative")
    return depth / 100.0 * fresh_snow_density_kg_m3


def synthetic_weather(
    *,
    name: str,
    duration_h: int,
    snowfall_peak_kg_m2_h: float,
    snowfall_hours: int,
    base_temperature_c: float,
    warming_c_per_day: float,
    repeated_events: int,
    rain_on_snow_mm: float,
    dt_hours: float = 1.0,
    rain_duration_h: float = 12.0,
) -> WeatherSeries:
    if dt_hours <= 0:
        raise ValueError("dt_hours must be positive")
    if repeated_events <= 0:
        raise ValueError("repeated_events must be positive")
    step_count = duration_h / dt_hours
    if not np.isclose(step_count, round(step_count)):
        raise ValueError("duration_h must be divisible by dt_hours")
    steps = int(round(step_count))
    time_h = np.arange(steps, dtype=float) * dt_hours
    temperature = (
        base_temperature_c
        + warming_c_per_day * time_h / 24.0
        + 2.0 * np.sin(2.0 * np.pi * (time_h - 8.0) / 24.0)
    )
    snowfall = np.zeros(steps, dtype=float)
    event_steps = max(1, int(round(snowfall_hours / repeated_events / dt_hours)))
    centers = np.linspace(0.12 * steps, 0.65 * steps, repeated_events)
    for center in centers:
        distance = (np.arange(steps) - center) / max(event_steps / 3.0, 1.0)
        snowfall += snowfall_peak_kg_m2_h * dt_hours * np.exp(-0.5 * distance**2)
    rain = np.zeros(steps, dtype=float)
    if rain_on_snow_mm > 0:
        warm_steps = np.flatnonzero(temperature > -0.5)
        if warm_steps.size:
            window_start_h = (warm_steps[-1] + 1) * dt_hours - rain_duration_h
            rain_steps = warm_steps[warm_steps * dt_hours >= window_start_h]
            rain[rain_steps] = rain_on_snow_mm / rain_steps.size
    return WeatherSeries(
        temperature_c=temperature,
        snowfall_kg_m2=snowfall,
        rain_mm=rain,
        dt_hours=dt_hours,
        name=name,
    )


def resample_weather(weather: WeatherSeries, dt_hours: float) -> WeatherSeries:
    if dt_hours <= 0:
        raise ValueError("dt_hours must be positive")
    if np.isclose(dt_hours, weather.dt_hours):
        return weather
    total_h = len(weather.temperature_c) * weather.dt_hours
    step_count = total_h / dt_hours
    if not np.isclose(step_count, round(step_count)):
        raise ValueError("new time step must divide the source duration exactly")
    new_steps = int(round(step_count))
    source_t = np.arange(len(weather.temperature_c)) * weather.dt_hours
    target_t = np.arange(new_steps) * dt_hours
    temperature = np.interp(target_t, source_t, weather.temperature_c)
    cumulative_snow = np.r_[0.0, np.cumsum(weather.snowfall_kg_m2)]
    cumulative_rain = np.r_[0.0, np.cumsum(weather.rain_mm)]
    source_edges = np.arange(len(weather.temperature_c) + 1) * weather.dt_hours
    target_edges = np.arange(new_steps + 1) * dt_hours
    snowfall = np.diff(np.interp(target_edges, source_edges, cumulative_snow))
    rain = np.diff(np.interp(target_edges, source_edges, cumulative_rain))
    return WeatherSeries(
        temperature_c=temperature,
        snowfall_kg_m2=snowfall,
        rain_mm=rain,
        dt_hours=dt_hours,
        name=f"{weather.name}_{dt_hours:g}h",
    )
