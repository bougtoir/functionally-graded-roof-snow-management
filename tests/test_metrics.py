from __future__ import annotations

import numpy as np

from graded_roof.metrics import (
    additive_epsilon_indicator,
    matched_objective_improvement,
    nondominated_mask,
    normalized_hypervolume_2d,
)


def test_nondominated_mask() -> None:
    points = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0], [3.0, 3.0]])
    np.testing.assert_array_equal(nondominated_mask(points), [True, True, True, False])


def test_hypervolume_is_bounded() -> None:
    points = np.array([[0.2, 0.8], [0.5, 0.4], [0.8, 0.2]])
    value = normalized_hypervolume_2d(points, (1.0, 1.0))
    assert 0 < value < 1


def test_epsilon_and_matched_improvement_detect_better_front() -> None:
    reference = np.array([[2.0, 4.0], [4.0, 2.0]])
    candidate = np.array([[1.0, 3.0], [3.0, 1.0]])
    assert additive_epsilon_indicator(candidate, reference) == -1.0
    improvement = matched_objective_improvement(candidate, reference)
    assert improvement["matched_l_improvement_median"] == 0.375
    assert improvement["matched_l_improvement_maximum"] == 0.5
    assert improvement["matched_s_improvement_median"] == 0.375
    assert improvement["matched_s_improvement_maximum"] == 0.5
