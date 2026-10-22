# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import pytest

from src.util.map import Area, _is_inside

SQUARE = Area(name="square", vertex_list=[[0, 0], [0, 10], [10, 10], [10, 0]])
FAR_SQUARE = Area(name="far_square", vertex_list=[[20, 20], [20, 30], [30, 30], [30, 20]])


@pytest.mark.parametrize("location", [[5, 5], [1, 1], [9.9, 9.9], [0.001, 5]])
def test_point_inside_square(location):
    assert _is_inside(location, [SQUARE]) is True


@pytest.mark.parametrize("location", [[15, 5], [-1, 5], [5, 11], [5, -0.001], [100, 100]])
def test_point_outside_square(location):
    assert _is_inside(location, [SQUARE]) is False


def test_vertex_order_does_not_matter():
    reversed_square = Area(name="reversed", vertex_list=list(reversed(SQUARE.vertex_list)))
    assert _is_inside([5, 5], [reversed_square]) is True
    assert _is_inside([15, 5], [reversed_square]) is False


def test_non_convex_polygon():
    l_shape = Area(name="l_shape", vertex_list=[[0, 0], [0, 10], [5, 10], [5, 5], [10, 5], [10, 0]])
    assert _is_inside([2, 8], [l_shape]) is True
    assert _is_inside([8, 2], [l_shape]) is True
    assert _is_inside([8, 8], [l_shape]) is False


def test_point_inside_one_of_several_areas():
    assert _is_inside([25, 25], [SQUARE, FAR_SQUARE]) is True
    assert _is_inside([5, 5], [SQUARE, FAR_SQUARE]) is True
    assert _is_inside([15, 15], [SQUARE, FAR_SQUARE]) is False


def test_empty_area_list():
    assert _is_inside([5, 5], []) is False


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        ([0, 5], True),  # left edge
        ([5, 0], True),  # bottom edge
        ([0, 0], True),  # bottom-left vertex
        ([10, 5], False),  # right edge
        ([5, 10], False),  # top edge
        ([10, 10], False),  # top-right vertex
    ],
)
def test_boundary_is_half_open(location, expected):
    """Ray casting includes the min edges and excludes the max edges."""
    assert _is_inside(location, [SQUARE]) is expected
