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
