from __future__ import annotations

import numpy as np
import pandas as pd

from graded_roof.config import load_config
from graded_roof.models import SimulationConfig, WeatherSeries
from graded_roof.optimization import variable_bounds
from graded_roof.reporting import design_from_row
from graded_roof.study import evaluate_design, interpolate_profile, uniform_design


def test_interpolate_profile_preserves_control_endpoints() -> None:
    profile = interpolate_profile(np.array([2.0, 8.0, 5.0]), cells=9)
    assert profile.shape == (9,)
    assert profile[0] == 2.0
    assert profile[-1] == 5.0


def test_evaluate_design_uses_worst_case_primary_objectives() -> None:
    config = {
        "roof": {"cells": 2, "length_m": 2.0, "width_m": 1.0},
        "surface": {"kinetic_ratio": 0.78},
    }
    design = uniform_design(
        config,
        slope_deg=0.0,
        mu_static=0.5,
        adhesion_pa=100.0,
        label="test",
    )
    weathers = [
        WeatherSeries(
            temperature_c=np.array([-5.0]),
            snowfall_kg_m2=np.array([10.0]),
            rain_mm=np.array([0.0]),
            dt_hours=1.0,
            name="low",
        ),
        WeatherSeries(
            temperature_c=np.array([-5.0]),
            snowfall_kg_m2=np.array([20.0]),
            rain_mm=np.array([0.0]),
            dt_hours=1.0,
            name="high",
        ),
    ]
    aggregate, scenarios = evaluate_design(design, weathers, SimulationConfig())
    assert aggregate["l_max_kg_per_m"] == 40.0
    assert aggregate["s_max_kg_per_m"] == 0.0
    assert len(scenarios) == 2


def test_joint_variable_bounds_cover_all_profile_properties() -> None:
    config = {
        "optimizer": {"profile_control_points": 4},
        "roof": {"slope_bounds_deg": [2.0, 45.0]},
        "surface": {
            "static_friction_bounds": [0.08, 0.65],
            "adhesion_bounds_pa": [0.0, 250.0],
        },
    }
    lower, upper = variable_bounds(config, "joint")
    assert lower.shape == (12,)
    assert upper.shape == (12,)
    np.testing.assert_allclose(lower[:4], 2.0)
    np.testing.assert_allclose(upper[-4:], 250.0)


def test_front_variables_are_reconstructed_in_numeric_order() -> None:
    config = load_config("config/production.yaml")
    values = np.array(
        [2.0, 10.0, 20.0, 30.0, 0.1, 0.2, 0.3, 0.4, 0.0, 50.0, 100.0, 150.0]
    )
    row = pd.Series({f"x_{index}": values[index] for index in range(12)})
    row = row.reindex(sorted(row.index))
    design = design_from_row(row, config, "joint")
    expected_slopes = interpolate_profile(
        values[:4],
        config["roof"]["cells"],
    )
    np.testing.assert_allclose(design.slope_deg, expected_slopes)
