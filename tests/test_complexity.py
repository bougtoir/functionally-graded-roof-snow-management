from __future__ import annotations

import numpy as np

from graded_roof.complexity import (
    design_complexity,
    manufacturable_mapping,
    map_surface_classes,
)
from graded_roof.models import RoofDesign


def test_surface_mapping_and_combined_segment_complexity() -> None:
    design = RoofDesign(
        slope_deg=np.array([10.1, 10.2, 20.0, 20.0]),
        mu_static=np.array([0.11, 0.12, 0.49, 0.50]),
        mu_kinetic=np.array([0.08, 0.09, 0.38, 0.39]),
        adhesion_pa=np.array([10.0, 20.0, 190.0, 200.0]),
        length_m=8.0,
    )
    classes = {
        "low": {
            "mu_static": 0.1,
            "mu_kinetic": 0.078,
            "adhesion_pa": 0.0,
        },
        "high": {
            "mu_static": 0.5,
            "mu_kinetic": 0.39,
            "adhesion_pa": 200.0,
        },
    }

    static, kinetic, adhesion, labels = map_surface_classes(design, classes)
    np.testing.assert_allclose(static, [0.1, 0.1, 0.5, 0.5])
    np.testing.assert_allclose(kinetic, [0.078, 0.078, 0.39, 0.39])
    np.testing.assert_allclose(adhesion, [0.0, 0.0, 200.0, 200.0])
    assert labels == ["low", "low", "high", "high"]

    complexity = design_complexity(
        design,
        classes,
        slope_rounding_deg=1.0,
    )
    assert complexity["transition_count"] == 1
    assert complexity["minimum_segment_cells"] == 2
    assert np.isclose(complexity["maximum_adjacent_slope_change_deg"], 9.8)


def test_manufacturable_mapping_enforces_segment_and_transition_limits() -> None:
    cells = 12
    design = RoofDesign(
        slope_deg=np.linspace(2.0, 45.0, cells),
        mu_static=np.linspace(0.1, 0.5, cells),
        mu_kinetic=np.linspace(0.08, 0.4, cells),
        adhesion_pa=np.linspace(0.0, 200.0, cells),
        length_m=8.0,
    )
    classes = {
        "low": {
            "mu_static": 0.1,
            "mu_kinetic": 0.078,
            "adhesion_pa": 0.0,
        },
        "high": {
            "mu_static": 0.5,
            "mu_kinetic": 0.39,
            "adhesion_pa": 200.0,
        },
    }
    mapped, _ = manufacturable_mapping(
        design,
        classes,
        slope_rounding_deg=1.0,
        minimum_segment_cells=3,
        maximum_transitions=3,
        maximum_adjacent_slope_change_deg=12.0,
    )
    complexity = design_complexity(
        mapped,
        classes,
        slope_rounding_deg=1.0,
    )
    assert complexity["minimum_segment_cells"] >= 3
    assert complexity["transition_count"] <= 3
    assert complexity["maximum_adjacent_slope_change_deg"] <= 12.0
