from __future__ import annotations

import numpy as np

from graded_roof.metrics import nondominated_mask, normalized_hypervolume_2d


def test_nondominated_mask() -> None:
    points = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0], [3.0, 3.0]])
    np.testing.assert_array_equal(nondominated_mask(points), [True, True, True, False])


def test_hypervolume_is_bounded() -> None:
    points = np.array([[0.2, 0.8], [0.5, 0.4], [0.8, 0.2]])
    value = normalized_hypervolume_2d(points, (1.0, 1.0))
    assert 0 < value < 1
