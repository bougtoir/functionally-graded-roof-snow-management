"""Continuous-time synthetic forcing aggregated consistently to any timestep.

The submitted analysis sampled snowfall and temperature at the start of each
numerical step.  Here every scenario is defined as a continuous function of
physical time; step totals of snowfall and rain are exact integrals (snowfall)
or aggregates of a 15-s reference grid (rain), and temperature is the step
mean.  Coarser steps therefore see the same physical forcing.
"""

from __future__ import annotations

import math

import numpy as np

from graded_roof.models import WeatherSeries

REFERENCE_DT_HOURS = 1.0 / 240.0


def _event_centers_h(duration_h: float, repeated_events: int) -> np.ndarray:
    return np.linspace(0.12 * duration_h, 0.65 * duration_h, repeated_events)


def snowfall_rate_kg_m2_h(t_h: np.ndarray, scenario: dict, duration_h: float) -> np.ndarray:
    sigma = scenario["snowfall_hours"] / scenario["repeated_events"] / 3.0
    rate = np.zeros_like(np.asarray(t_h, dtype=float))
    for center in _event_centers_h(duration_h, scenario["repeated_events"]):
        rate += scenario["snowfall_peak_kg_m2_h"] * np.exp(-0.5 * ((t_h - center) / sigma) ** 2)
    return rate


def _snowfall_integral(t_h: np.ndarray, scenario: dict, duration_h: float) -> np.ndarray:
    sigma = scenario["snowfall_hours"] / scenario["repeated_events"] / 3.0
    total = np.zeros_like(np.asarray(t_h, dtype=float))
    erf = np.vectorize(math.erf)
    for center in _event_centers_h(duration_h, scenario["repeated_events"]):
        total += (
            scenario["snowfall_peak_kg_m2_h"]
            * sigma
            * math.sqrt(math.pi / 2.0)
            * (1.0 + erf((t_h - center) / (sigma * math.sqrt(2.0))))
        )
    return total


def temperature_c(t_h: np.ndarray, scenario: dict) -> np.ndarray:
    return (
        scenario["base_temperature_c"]
        + scenario["warming_c_per_day"] * t_h / 24.0
        + 2.0 * np.sin(2.0 * np.pi * (t_h - 8.0) / 24.0)
    )


def _reference_rain(scenario: dict, duration_h: float, rain_duration_h: float) -> np.ndarray:
    steps = int(round(duration_h / REFERENCE_DT_HOURS))
    mid = (np.arange(steps) + 0.5) * REFERENCE_DT_HOURS
    rain = np.zeros(steps)
    if scenario.get("rain_on_snow_mm", 0.0) > 0:
        warm = np.flatnonzero(temperature_c(mid, scenario) > -0.5)
        if warm.size:
            end_h = (warm[-1] + 1) * REFERENCE_DT_HOURS
            chosen = warm[mid[warm] >= end_h - rain_duration_h]
            rain[chosen] = scenario["rain_on_snow_mm"] / chosen.size
    return rain


def continuous_synthetic_weather(
    scenario: dict,
    *,
    duration_h: float,
    dt_hours: float,
    rain_duration_h: float = 12.0,
    snowfall_factor: float = 1.0,
    temperature_offset_c: float = 0.0,
) -> WeatherSeries:
    steps_float = duration_h / dt_hours
    if not np.isclose(steps_float, round(steps_float)):
        raise ValueError("duration must be divisible by dt")
    steps = int(round(steps_float))
    ratio = dt_hours / REFERENCE_DT_HOURS
    if not np.isclose(ratio, round(ratio)):
        raise ValueError("dt must be a multiple of the 15-s reference step")
    ratio = int(round(ratio))
    edges = np.arange(steps + 1) * dt_hours
    snowfall = np.diff(_snowfall_integral(edges, scenario, duration_h)) * snowfall_factor
    fine_edges = np.arange(steps * ratio + 1) * REFERENCE_DT_HOURS
    fine_mid = 0.5 * (fine_edges[:-1] + fine_edges[1:])
    temperature = temperature_c(fine_mid, scenario).reshape(steps, ratio).mean(axis=1)
    rain = _reference_rain(scenario, duration_h, rain_duration_h).reshape(steps, ratio).sum(axis=1)
    return WeatherSeries(
        temperature_c=temperature + temperature_offset_c,
        snowfall_kg_m2=np.maximum(snowfall, 0.0),
        rain_mm=rain,
        dt_hours=dt_hours,
        name=scenario["name"],
    )
