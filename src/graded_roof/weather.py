from __future__ import annotations

import numpy as np

from graded_roof.models import WeatherSeries


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
) -> WeatherSeries:
    steps = int(round(duration_h / dt_hours))
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
            rain[warm_steps[-min(12, warm_steps.size) :]] = rain_on_snow_mm / min(
                12, warm_steps.size
            )
    return WeatherSeries(
        temperature_c=temperature,
        snowfall_kg_m2=snowfall,
        rain_mm=rain,
        dt_hours=dt_hours,
        name=name,
    )


def resample_weather(weather: WeatherSeries, dt_hours: float) -> WeatherSeries:
    if np.isclose(dt_hours, weather.dt_hours):
        return weather
    total_h = len(weather.temperature_c) * weather.dt_hours
    new_steps = int(round(total_h / dt_hours))
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
