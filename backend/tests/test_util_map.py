# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import pytest

from src.util.map import Area, _is_inside

SQUARE = Area("square", [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]])
SQUARE_CCW = Area("square_ccw", list(reversed(SQUARE.vertex_list)))
TRIANGLE = Area("triangle", [[0.0, 0.0], [10.0, 0.0], [5.0, 10.0]])
FAR_SQUARE = Area("far", [[100.0, 100.0], [110.0, 100.0], [110.0, 110.0], [100.0, 110.0]])
# U shape: notch between x=4..6 from y=3 up to y=10
U_SHAPE = Area("u", [[0, 0], [10, 0], [10, 10], [6, 10], [6, 3], [4, 3], [4, 10], [0, 10]])


@pytest.mark.parametrize("area", [SQUARE, SQUARE_CCW], ids=["cw", "ccw"])
@pytest.mark.parametrize("point, expected", [
    ([5.0, 5.0], True),
    ([0.1, 9.9], True),
    ([-1.0, 5.0], False),
    ([11.0, 5.0], False),
    ([5.0, -1.0], False),
    ([5.0, 11.0], False),
])
def test_square_inside_and_outside(area, point, expected):
    assert _is_inside(point, [area]) is expected


def test_triangle():
    assert _is_inside([5.0, 2.0], [TRIANGLE]) is True
    assert _is_inside([1.0, 8.0], [TRIANGLE]) is False
    assert _is_inside([9.0, 8.0], [TRIANGLE]) is False


def test_concave_polygon_notch_is_outside():
    assert _is_inside([5.0, 5.0], [U_SHAPE]) is False
    assert _is_inside([5.0, 1.0], [U_SHAPE]) is True
    assert _is_inside([2.0, 8.0], [U_SHAPE]) is True
    assert _is_inside([8.0, 8.0], [U_SHAPE]) is True


def test_empty_area_list_is_outside():
    assert _is_inside([5.0, 5.0], []) is False


def test_area_with_no_vertices_is_outside():
    assert _is_inside([5.0, 5.0], [Area("empty", [])]) is False


def test_any_matching_area_is_inside():
    assert _is_inside([105.0, 105.0], [SQUARE, FAR_SQUARE]) is True
    assert _is_inside([5.0, 5.0], [SQUARE, FAR_SQUARE]) is True
    assert _is_inside([50.0, 50.0], [SQUARE, FAR_SQUARE]) is False


def test_overlapping_areas_do_not_cancel_each_other():
    # Parity is not reset per area, but the loop stops at the first area that contains the point.
    assert _is_inside([5.0, 5.0], [SQUARE, SQUARE_CCW]) is True


def test_edges_use_half_open_rule():
    assert _is_inside([0.0, 5.0], [SQUARE]) is True    # left edge
    assert _is_inside([5.0, 0.0], [SQUARE]) is True    # bottom edge
    assert _is_inside([10.0, 5.0], [SQUARE]) is False  # right edge
    assert _is_inside([5.0, 10.0], [SQUARE]) is False  # top edge


def test_accepts_tuple_location():
    assert _is_inside((5.0, 5.0), [SQUARE]) is True
