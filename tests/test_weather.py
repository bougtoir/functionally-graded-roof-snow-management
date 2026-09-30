from __future__ import annotations

import numpy as np
import pytest

from graded_roof.models import WeatherSeries
from graded_roof.weather import (
    resample_weather,
    snowfall_depth_to_mass,
    synthetic_weather,
)


def test_resample_preserves_snowfall_and_rain_totals() -> None:
    weather = WeatherSeries(
        temperature_c=np.array([-2.0, -1.0, 0.0, 1.0]),
        snowfall_kg_m2=np.array([0.0, 0.0, 3.0, 9.0]),
        rain_mm=np.array([0.0, 1.0, 0.0, 5.0]),
        dt_hours=1.0,
    )
    resampled = resample_weather(weather, 2.0)
    assert resampled.snowfall_kg_m2.sum() == pytest.approx(12.0)
    assert resampled.rain_mm.sum() == pytest.approx(6.0)


def test_resample_rejects_a_step_that_truncates_the_source_period() -> None:
    weather = WeatherSeries(
        temperature_c=np.zeros(3),
        snowfall_kg_m2=np.array([0.0, 0.0, 9.0]),
        rain_mm=np.zeros(3),
        dt_hours=1.0,
    )
    with pytest.raises(ValueError, match="divide the source duration"):
        resample_weather(weather, 2.1)


def test_synthetic_rain_window_is_invariant_across_time_steps() -> None:
    scenarios = [
        synthetic_weather(
            name=f"rain_{dt:g}",
            duration_h=48,
            snowfall_peak_kg_m2_h=1.0,
            snowfall_hours=6,
            base_temperature_c=2.0,
            warming_c_per_day=0.0,
            repeated_events=1,
            rain_on_snow_mm=12.0,
            dt_hours=dt,
        )
        for dt in (0.5, 1.0, 2.0)
    ]
    for weather in scenarios:
        rain_indices = np.flatnonzero(weather.rain_mm > 0)
        assert weather.rain_mm.sum() == pytest.approx(12.0)
        assert rain_indices.size * weather.dt_hours == pytest.approx(12.0)
        assert rain_indices[0] * weather.dt_hours == pytest.approx(36.0)


def test_snowfall_depth_conversion_uses_fresh_snow_density() -> None:
    depth_cm = np.array([0.0, 2.5, 10.0])
    np.testing.assert_allclose(
        snowfall_depth_to_mass(depth_cm, fresh_snow_density_kg_m3=120.0),
        np.array([0.0, 3.0, 12.0]),
    )
