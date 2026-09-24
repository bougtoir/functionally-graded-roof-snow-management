from __future__ import annotations

import numpy as np

from graded_roof.models import RoofDesign


def map_surface_classes(
    design: RoofDesign,
    classes: dict[str, dict[str, float]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    names = list(classes)
    values = np.array(
        [[classes[name]["mu_static"], classes[name]["adhesion_pa"]] for name in names]
    )
    scale = np.ptp(values, axis=0)
    target = np.column_stack([design.mu_static, design.adhesion_pa])
    distances = np.linalg.norm(
        (target[:, None, :] - values[None, :, :])
        / np.where(scale > 0, scale, 1.0),
        axis=2,
    )
    indices = np.argmin(distances, axis=1)
    return (
        values[indices, 0],
        np.array([classes[names[index]]["mu_kinetic"] for index in indices]),
        values[indices, 1],
        [names[index] for index in indices],
    )


def manufacturable_mapping(
    design: RoofDesign,
    classes: dict[str, dict[str, float]],
    *,
    slope_rounding_deg: float,
    minimum_segment_cells: int,
    maximum_transitions: int,
    maximum_adjacent_slope_change_deg: float,
) -> tuple[RoofDesign, list[str]]:
    _, _, _, mapped_labels = map_surface_classes(design, classes)
    segment_count = min(
        maximum_transitions + 1,
        max(1, design.cells // minimum_segment_cells),
    )
    segment_indices = np.array_split(np.arange(design.cells), segment_count)
    slope = np.empty(design.cells)
    labels: list[str] = [""] * design.cells
    previous_slope: float | None = None
    for indices in segment_indices:
        segment_slope = (
            np.round(np.median(design.slope_deg[indices]) / slope_rounding_deg)
            * slope_rounding_deg
        )
        if previous_slope is not None:
            segment_slope = float(
                np.clip(
                    segment_slope,
                    previous_slope - maximum_adjacent_slope_change_deg,
                    previous_slope + maximum_adjacent_slope_change_deg,
                )
            )
        segment_labels = [mapped_labels[index] for index in indices]
        segment_label = max(
            classes,
            key=lambda label: segment_labels.count(label),
        )
        slope[indices] = segment_slope
        for index in indices:
            labels[index] = segment_label
        previous_slope = float(segment_slope)
    mu_static = np.array([classes[label]["mu_static"] for label in labels])
    mu_kinetic = np.array([classes[label]["mu_kinetic"] for label in labels])
    adhesion = np.array([classes[label]["adhesion_pa"] for label in labels])
    return (
        RoofDesign(
            slope_deg=slope,
            mu_static=mu_static,
            mu_kinetic=mu_kinetic,
            adhesion_pa=adhesion,
            length_m=design.length_m,
            width_m=design.width_m,
            label=f"{design.label}_manufacturable",
        ),
        labels,
    )


def _minimum_run_length(values: list[object]) -> int:
    if not values:
        return 0
    lengths = []
    current = values[0]
    length = 1
    for value in values[1:]:
        if value == current:
            length += 1
        else:
            lengths.append(length)
            current = value
            length = 1
    lengths.append(length)
    return min(lengths)


def design_complexity(
    design: RoofDesign,
    classes: dict[str, dict[str, float]],
    *,
    slope_rounding_deg: float,
) -> dict[str, float | int]:
    _, _, _, material_labels = map_surface_classes(design, classes)
    rounded_slope = (
        np.round(design.slope_deg / slope_rounding_deg) * slope_rounding_deg
    )
    combined_labels = list(zip(rounded_slope.tolist(), material_labels, strict=True))
    transitions = sum(
        first != second
        for first, second in zip(combined_labels[:-1], combined_labels[1:], strict=True)
    )
    return {
        "slope_total_variation_deg": float(np.abs(np.diff(design.slope_deg)).sum()),
        "surface_total_variation": float(np.abs(np.diff(design.mu_static)).sum()),
        "maximum_adjacent_slope_change_deg": float(
            np.abs(np.diff(design.slope_deg)).max(initial=0.0)
        ),
        "transition_count": transitions,
        "minimum_segment_cells": _minimum_run_length(combined_labels),
    }
