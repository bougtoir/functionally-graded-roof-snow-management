import numpy as np
import pandas as pd

from graded_roof.jma import daily_weather, parse_jma_numeric


def test_daily_weather_converts_snow_depth_and_separates_warm_rain() -> None:
    frame = pd.DataFrame(
        {
            "mean_temperature_c": [-5.0, 3.0, 0.0],
            "snowfall_depth_cm": [10.0, 0.0, 2.0],
            "precipitation_mm": [8.0, 7.0, 3.0],
        }
    )
    weather = daily_weather(
        frame,
        fresh_snow_density_kg_m3=100.0,
        name="jma_test",
    )
    np.testing.assert_allclose(weather.snowfall_kg_m2, [10.0, 0.0, 2.0])
    np.testing.assert_allclose(weather.rain_mm, [0.0, 7.0, 0.0])
    assert weather.dt_hours == 24.0


def test_jma_quality_markers_preserve_no_snow_as_zero() -> None:
    assert parse_jma_numeric("-- )") == 0.0
    assert parse_jma_numeric("8.0 ]") == 8.0
    assert np.isnan(parse_jma_numeric("///"))
