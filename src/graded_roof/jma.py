from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from graded_roof.models import WeatherSeries
from graded_roof.weather import snowfall_depth_to_mass


def _find_column(
    columns: pd.MultiIndex,
    required_terms: tuple[str, ...],
) -> tuple[str, ...]:
    for column in columns:
        text = "|".join(str(level) for level in column)
        if all(term in text for term in required_terms):
            return column
    raise ValueError(f"JMA column not found: {required_terms}")


def parse_jma_numeric(value: object) -> float:
    text = str(value).strip()
    if text.startswith("--"):
        return 0.0
    if text in {"", "nan", "///", "×"}:
        return float("nan")
    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", text)
    return float(match.group()) if match else float("nan")


def parse_daily_html(path: Path, station_id: str, year: int, month: int) -> pd.DataFrame:
    tables = pd.read_html(path)
    data = next(table for table in tables if isinstance(table.columns, pd.MultiIndex))
    day_column = data.columns[0]
    temperature_column = _find_column(data.columns, ("気温", "平均"))
    precipitation_column = _find_column(data.columns, ("降水量", "合計"))
    snowfall_column = _find_column(data.columns, ("雪(cm)", "降雪", "合計"))
    depth_column = _find_column(data.columns, ("雪(cm)", "最深積雪"))
    parsed = pd.DataFrame(
        {
            "station_id": station_id,
            "date": pd.to_datetime(
                {
                    "year": year,
                    "month": month,
                    "day": data[day_column].map(parse_jma_numeric),
                },
                errors="coerce",
            ),
            "mean_temperature_c_raw": data[temperature_column].astype(str),
            "precipitation_mm_raw": data[precipitation_column].astype(str),
            "snowfall_depth_cm_raw": data[snowfall_column].astype(str),
            "ground_snow_depth_cm_raw": data[depth_column].astype(str),
            "mean_temperature_c": data[temperature_column].map(parse_jma_numeric),
            "precipitation_mm": data[precipitation_column].map(parse_jma_numeric),
            "snowfall_depth_cm": data[snowfall_column].map(parse_jma_numeric),
            "ground_snow_depth_cm": data[depth_column].map(parse_jma_numeric),
        }
    )
    return parsed.dropna(subset=["date"]).reset_index(drop=True)


def daily_weather(
    frame: pd.DataFrame,
    *,
    fresh_snow_density_kg_m3: float,
    name: str,
) -> WeatherSeries:
    temperature = frame["mean_temperature_c"].to_numpy(dtype=float)
    snowfall_depth = frame["snowfall_depth_cm"].fillna(0.0).to_numpy(dtype=float)
    precipitation = frame["precipitation_mm"].fillna(0.0).to_numpy(dtype=float)
    snowfall = snowfall_depth_to_mass(
        snowfall_depth,
        fresh_snow_density_kg_m3,
    )
    rain = np.where((temperature > 1.0) & (snowfall_depth == 0.0), precipitation, 0.0)
    valid_temperature = np.isfinite(temperature)
    if not np.all(valid_temperature):
        temperature = pd.Series(temperature).interpolate(limit_direction="both").to_numpy()
    return WeatherSeries(
        temperature_c=temperature,
        snowfall_kg_m2=snowfall,
        rain_mm=rain,
        dt_hours=24.0,
        name=name,
    )
