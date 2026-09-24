from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class WeatherSeries:
    temperature_c: FloatArray
    snowfall_kg_m2: FloatArray
    rain_mm: FloatArray
    dt_hours: float
    name: str = "weather"

    def __post_init__(self) -> None:
        lengths = {
            len(self.temperature_c),
            len(self.snowfall_kg_m2),
            len(self.rain_mm),
        }
        if len(lengths) != 1:
            raise ValueError("weather arrays must have equal length")
        if self.dt_hours <= 0:
            raise ValueError("dt_hours must be positive")
        if np.any(self.snowfall_kg_m2 < 0) or np.any(self.rain_mm < 0):
            raise ValueError("snowfall and rain cannot be negative")


@dataclass(frozen=True)
class RoofDesign:
    slope_deg: FloatArray
    mu_static: FloatArray
    mu_kinetic: FloatArray
    adhesion_pa: FloatArray
    length_m: float
    width_m: float = 1.0
    label: str = "design"

    def __post_init__(self) -> None:
        lengths = {
            len(self.slope_deg),
            len(self.mu_static),
            len(self.mu_kinetic),
            len(self.adhesion_pa),
        }
        if len(lengths) != 1 or not self.slope_deg.size:
            raise ValueError("roof design arrays must have equal nonzero length")
        if self.length_m <= 0 or self.width_m <= 0:
            raise ValueError("roof dimensions must be positive")
        if np.any((self.slope_deg < 0) | (self.slope_deg >= 90)):
            raise ValueError("slopes must be in [0, 90) degrees")
        if np.any(self.mu_static < 0) or np.any(self.mu_kinetic < 0):
            raise ValueError("friction coefficients cannot be negative")
        if np.any(self.adhesion_pa < 0):
            raise ValueError("adhesion cannot be negative")

    @property
    def cells(self) -> int:
        return int(self.slope_deg.size)

    @property
    def cell_area_m2(self) -> float:
        return self.length_m * self.width_m / self.cells

    @classmethod
    def uniform(
        cls,
        cells: int,
        length_m: float,
        slope_deg: float,
        mu_static: float,
        mu_kinetic: float,
        adhesion_pa: float,
        label: str = "uniform",
    ) -> RoofDesign:
        return cls(
            slope_deg=np.full(cells, slope_deg, dtype=float),
            mu_static=np.full(cells, mu_static, dtype=float),
            mu_kinetic=np.full(cells, mu_kinetic, dtype=float),
            adhesion_pa=np.full(cells, adhesion_pa, dtype=float),
            length_m=length_m,
            label=label,
        )


@dataclass(frozen=True)
class SimulationConfig:
    gravity_m_s2: float = 9.80665
    melt_factor_kg_m2_c_h: float = 0.12
    rain_heat_factor_kg_m2_mm: float = 0.02
    initial_density_kg_m3: float = 120.0
    maximum_density_kg_m3: float = 420.0
    compaction_rate_per_day: float = 0.035
    dynamic_friction_age_scale_days: float = 5.0
    friction_age_gain: float = 0.18
    near_melt_friction_loss: float = 0.22
    near_melt_center_c: float = -0.5
    near_melt_width_c: float = 1.8
    friction_model: str = "dynamic"
    transport_fraction_limit: float = 1.0
    event_threshold_kg_per_m: float = 0.1
    intervention_mass_kg_per_m: float = 800.0

    def __post_init__(self) -> None:
        if self.friction_model not in {"constant", "dynamic"}:
            raise ValueError("friction_model must be constant or dynamic")
        if self.dynamic_friction_age_scale_days <= 0:
            raise ValueError("dynamic_friction_age_scale_days must be positive")
        if self.friction_age_gain < 0:
            raise ValueError("friction_age_gain cannot be negative")
        if not 0 <= self.near_melt_friction_loss < 1:
            raise ValueError("near_melt_friction_loss must be in [0, 1)")
        if self.near_melt_width_c <= 0:
            raise ValueError("near_melt_width_c must be positive")
        if not 0 < self.transport_fraction_limit <= 1:
            raise ValueError("transport_fraction_limit must be in (0, 1]")


@dataclass(frozen=True)
class SimulationResult:
    roof_mass_kg_per_m: FloatArray
    pre_release_roof_mass_kg_per_m: FloatArray
    pre_release_max_depth_m: FloatArray
    shed_mass_kg_per_m: FloatArray
    melt_mass_kg_per_m: FloatArray
    density_kg_m3: FloatArray
    final_cell_mass_kg_per_m: FloatArray
    input_snow_kg_per_m: float
    l_max_kg_per_m: float
    s_max_kg_per_m: float
    ssci: float
    total_shed_kg_per_m: float
    shed_event_count: int
    kinetic_energy_proxy_j_per_m: float
    time_above_intervention_h: float
    manual_triggers: int
    residual_mass_kg_per_m: float
    mass_balance_error_kg_per_m: float
    maximum_snow_depth_m: float
