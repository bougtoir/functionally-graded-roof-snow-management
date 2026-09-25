from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def ssci(event_masses: ArrayLike) -> float:
    events = np.asarray(event_masses, dtype=float)
    events = events[events > 0]
    total = float(events.sum())
    if total == 0:
        return 0.0
    return float(np.square(events / total).sum())


def nondominated_mask(points: ArrayLike) -> np.ndarray:
    values = np.asarray(points, dtype=float)
    if values.ndim != 2:
        raise ValueError("points must be a two-dimensional array")
    mask = np.ones(values.shape[0], dtype=bool)
    for i, point in enumerate(values):
        if not mask[i]:
            continue
        dominates_i = np.all(values <= point, axis=1) & np.any(values < point, axis=1)
        if np.any(dominates_i):
            mask[i] = False
    return mask


def total_variation(values: ArrayLike) -> float:
    array = np.asarray(values, dtype=float)
    return float(np.abs(np.diff(array)).sum())


def transition_count(values: ArrayLike, tolerance: float = 1e-9) -> int:
    array = np.asarray(values, dtype=float)
    return int(np.count_nonzero(np.abs(np.diff(array)) > tolerance))


def normalized_hypervolume_2d(points: ArrayLike, reference: tuple[float, float]) -> float:
    values = np.asarray(points, dtype=float)
    values = values[nondominated_mask(values)]
    if not values.size:
        return 0.0
    scale = np.asarray(reference, dtype=float)
    normalized = np.clip(values / scale, 0.0, 1.0)
    normalized = normalized[np.argsort(normalized[:, 0])]
    area = 0.0
    previous_y = 1.0
    for x_value, y_value in normalized:
        if y_value < previous_y:
            area += (1.0 - x_value) * (previous_y - y_value)
            previous_y = y_value
    return float(area)


def additive_epsilon_indicator(
    approximation: ArrayLike,
    reference: ArrayLike,
) -> float:
    approximation_values = np.asarray(approximation, dtype=float)
    reference_values = np.asarray(reference, dtype=float)
    if approximation_values.ndim != 2 or reference_values.ndim != 2:
        raise ValueError("fronts must be two-dimensional arrays")
    if approximation_values.shape[1] != reference_values.shape[1]:
        raise ValueError("fronts must have the same objective count")
    if not approximation_values.size or not reference_values.size:
        raise ValueError("fronts cannot be empty")
    distances = (
        approximation_values[:, None, :] - reference_values[None, :, :]
    )
    return float(np.max(np.min(np.max(distances, axis=2), axis=0)))


def matched_objective_improvement(
    candidate: ArrayLike,
    reference: ArrayLike,
) -> dict[str, float]:
    candidate_values = np.asarray(candidate, dtype=float)
    reference_values = np.asarray(reference, dtype=float)
    l_improvements: list[float] = []
    s_improvements: list[float] = []
    for reference_point in reference_values:
        matched_s = candidate_values[
            candidate_values[:, 1] <= reference_point[1] + 1e-12
        ]
        if matched_s.size and abs(reference_point[0]) > 1e-12:
            l_improvements.append(
                float(
                    (reference_point[0] - matched_s[:, 0].min())
                    / abs(reference_point[0])
                )
            )
        matched_l = candidate_values[
            candidate_values[:, 0] <= reference_point[0] + 1e-12
        ]
        if matched_l.size and abs(reference_point[1]) > 1e-12:
            s_improvements.append(
                float(
                    (reference_point[1] - matched_l[:, 1].min())
                    / abs(reference_point[1])
                )
            )
    return {
        "matched_l_improvement_median": (
            float(np.median(l_improvements)) if l_improvements else float("nan")
        ),
        "matched_l_improvement_maximum": (
            float(np.max(l_improvements)) if l_improvements else float("nan")
        ),
        "matched_s_improvement_median": (
            float(np.median(s_improvements)) if s_improvements else float("nan")
        ),
        "matched_s_improvement_maximum": (
            float(np.max(s_improvements)) if s_improvements else float("nan")
        ),
    }
