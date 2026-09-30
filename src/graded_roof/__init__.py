"""Functionally graded roof snow-management simulation."""

from graded_roof.models import RoofDesign, SimulationConfig, SimulationResult, WeatherSeries
from graded_roof.simulation import simulate

__all__ = [
    "RoofDesign",
    "SimulationConfig",
    "SimulationResult",
    "WeatherSeries",
    "simulate",
]
