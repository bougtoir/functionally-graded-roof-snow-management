from __future__ import annotations

import numpy as np

from graded_roof.metrics import ssci
from graded_roof.models import RoofDesign, SimulationConfig, WeatherSeries
from graded_roof.simulation import simulate


def weather(snowfall: np.ndarray, temperature: float = -5.0) -> WeatherSeries:
    return WeatherSeries(
        temperature_c=np.full(snowfall.size, temperature),
        snowfall_kg_m2=snowfall.astype(float),
        rain_mm=np.zeros(snowfall.size),
        dt_hours=1.0,
        name="test",
    )


def test_mass_conservation() -> None:
    design = RoofDesign.uniform(8, 8.0, 30.0, 0.15, 0.1, 0.0)
    result = simulate(design, weather(np.r_[np.full(4, 5.0), np.zeros(20)]), SimulationConfig())
    assert abs(result.mass_balance_error_kg_per_m) < 1e-8


def test_sliding_threshold() -> None:
    snow = weather(np.r_[10.0, np.zeros(4)])
    retaining = RoofDesign.uniform(4, 4.0, 10.0, 0.6, 0.45, 100.0)
    shedding = RoofDesign.uniform(4, 4.0, 40.0, 0.05, 0.03, 0.0)
    retaining_result = simulate(retaining, snow, SimulationConfig(friction_model="constant"))
    shedding_result = simulate(shedding, snow, SimulationConfig(friction_model="constant"))
    assert retaining_result.total_shed_kg_per_m == 0
    assert shedding_result.total_shed_kg_per_m > 0


def test_flat_roof_retains_without_melt() -> None:
    design = RoofDesign.uniform(5, 5.0, 0.0, 0.0, 0.0, 0.0)
    result = simulate(design, weather(np.full(3, 2.0)), SimulationConfig())
    assert result.total_shed_kg_per_m == 0
    assert np.isclose(result.residual_mass_kg_per_m, result.input_snow_kg_per_m)


def test_zero_friction_slope_sheds() -> None:
    design = RoofDesign.uniform(3, 3.0, 35.0, 0.0, 0.0, 0.0)
    result = simulate(design, weather(np.r_[8.0, np.zeros(5)]), SimulationConfig())
    assert result.total_shed_kg_per_m > 0


def test_ssci_identities() -> None:
    assert ssci([]) == 0
    assert ssci([10.0]) == 1
    assert np.isclose(ssci([5.0, 5.0]), 0.5)
    assert np.isclose(ssci([2.0, 2.0, 2.0, 2.0]), 0.25)


def test_deterministic_reproducibility() -> None:
    design = RoofDesign.uniform(6, 6.0, 25.0, 0.2, 0.15, 20.0)
    forcing = weather(np.linspace(0.0, 6.0, 12))
    first = simulate(design, forcing, SimulationConfig())
    second = simulate(design, forcing, SimulationConfig())
    np.testing.assert_array_equal(first.roof_mass_kg_per_m, second.roof_mass_kg_per_m)
    np.testing.assert_array_equal(first.shed_mass_kg_per_m, second.shed_mass_kg_per_m)


def test_sanity_monotonic_tendencies() -> None:
    forcing = weather(np.r_[np.full(6, 5.0), np.zeros(18)])
    low_slope = RoofDesign.uniform(8, 8.0, 8.0, 0.3, 0.22, 40.0)
    high_slope = RoofDesign.uniform(8, 8.0, 38.0, 0.3, 0.22, 40.0)
    low_friction = RoofDesign.uniform(8, 8.0, 30.0, 0.1, 0.07, 0.0)
    high_friction = RoofDesign.uniform(8, 8.0, 30.0, 0.6, 0.45, 150.0)
    config = SimulationConfig(friction_model="constant")
    assert simulate(high_slope, forcing, config).total_shed_kg_per_m >= simulate(
        low_slope, forcing, config
    ).total_shed_kg_per_m
    assert simulate(low_friction, forcing, config).total_shed_kg_per_m >= simulate(
        high_friction, forcing, config
    ).total_shed_kg_per_m
