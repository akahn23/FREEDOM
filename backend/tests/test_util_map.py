# SPDX-License-Identifier: Apache-2.0
"""Unit tests for src.util.map (Area and _is_inside)."""

import dataclasses

import pytest

import src.util
from src.util import map as util_map
from src.util.map import Area, _is_inside

SQUARE = Area("square", [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
SQUARE_CW = Area("square_cw", list(reversed(SQUARE.vertex_list)))
# Concave "U" shape: the notch 1<x<2, 1<y<3 is outside.
U_SHAPE = Area(
    "u",
    [[0, 0], [3, 0], [3, 3], [2, 3], [2, 1], [1, 1], [1, 3], [0, 3]],
)
TRIANGLE = Area("triangle", [[0, 0], [4, 0], [2, 4]])
FAR_SQUARE = Area("far", [[10, 10], [11, 10], [11, 11], [10, 11]])


def test_package_exposes_map_module():
    assert src.util.map is util_map


def test_area_fields():
    area = Area("zone", [[1.0, 2.0]])
    assert area.name == "zone"
    assert area.vertex_list == [[1.0, 2.0]]
    assert [f.name for f in dataclasses.fields(Area)] == ["name", "vertex_list"]
    assert area == Area("zone", [[1.0, 2.0]])


@pytest.mark.parametrize("args", [(), ("only_name",)])
def test_area_requires_all_fields(args):
    with pytest.raises(TypeError):
        Area(*args)


@pytest.mark.parametrize("area", [SQUARE, SQUARE_CW], ids=["ccw", "cw"])
@pytest.mark.parametrize(
    "location, expected",
    [
        ([0.5, 0.5], True),
        ([0.001, 0.999], True),
        ([1.5, 0.5], False),
        ([-0.5, 0.5], False),
        ([0.5, 1.5], False),
        ([0.5, -0.5], False),
        ([2.0, 2.0], False),
    ],
)
def test_is_inside_square_either_winding(area, location, expected):
    assert _is_inside(location, [area]) is expected


@pytest.mark.parametrize(
    "location, expected",
    [
        # Half-open rule: left (min x) and bottom (min y) edges are inside,
        # right (max x) and top (max y) edges are outside.
        ([0.0, 0.5], True),
        ([0.5, 0.0], True),
        ([1.0, 0.5], False),
        ([0.5, 1.0], False),
        # Corners follow the same rule: only the bottom-left corner is inside.
        ([0.0, 0.0], True),
        ([1.0, 0.0], False),
        ([0.0, 1.0], False),
        ([1.0, 1.0], False),
        # Just inside / just outside each edge.
        ([1e-9, 0.5], True),
        ([-1e-9, 0.5], False),
        ([1 - 1e-9, 0.5], True),
        ([1 + 1e-9, 0.5], False),
        ([0.5, 1 - 1e-9], True),
        ([0.5, -1e-9], False),
    ],
)
def test_is_inside_half_open_boundaries(location, expected):
    assert _is_inside(location, [SQUARE]) is expected
    assert _is_inside(location, [SQUARE_CW]) is expected


@pytest.mark.parametrize(
    "location, expected",
    [
        ([0.5, 2.0], True),
        ([2.5, 2.0], True),
        ([1.5, 0.5], True),
        ([1.5, 2.0], False),
        ([1.5, 2.9], False),
        ([3.5, 1.0], False),
    ],
)
def test_is_inside_concave_polygon(location, expected):
    assert _is_inside(location, [U_SHAPE]) is expected


@pytest.mark.parametrize(
    "location, expected",
    [
        ([2, 2], True),
        ([2, 3.9], True),
        ([0.5, 3], False),
        ([3.5, 3], False),
        ([2, 4], False),
    ],
)
def test_is_inside_triangle(location, expected):
    assert _is_inside(location, [TRIANGLE]) is expected


def test_is_inside_accepts_tuple_location_and_int_coordinates():
    assert _is_inside((1, 1), [TRIANGLE]) is True


@pytest.mark.parametrize(
    "area_list, expected",
    [
        ([SQUARE, FAR_SQUARE], True),
        ([FAR_SQUARE, SQUARE], True),
        ([FAR_SQUARE], False),
        ([FAR_SQUARE, FAR_SQUARE], False),
    ],
)
def test_is_inside_any_of_multiple_areas(area_list, expected):
    assert _is_inside([0.5, 0.5], area_list) is expected


def test_is_inside_parity_does_not_leak_between_areas():
    # Two outside areas must not combine into an "inside" result.
    left = Area("left", [[-3, 0], [-2, 0], [-2, 1], [-3, 1]])
    right = Area("right", [[2, 0], [3, 0], [3, 1], [2, 1]])
    assert _is_inside([0.5, 0.5], [left, right]) is False
    assert _is_inside([0.5, 0.5], [right, left]) is False


def test_is_inside_overlapping_areas_counts_as_inside():
    overlap = Area("overlap", [[0.25, 0.25], [0.75, 0.25], [0.75, 0.75], [0.25, 0.75]])
    assert _is_inside([0.5, 0.5], [SQUARE, overlap]) is True


@pytest.mark.parametrize(
    "area_list",
    [
        [],
        [Area("empty", [])],
        [Area("point", [[0.5, 0.5]])],
        [Area("segment", [[0, 0], [1, 1]])],
        [Area("horizontal", [[0, 0.5], [1, 0.5]])],
        [Area("collinear", [[0, 0], [1, 1], [2, 2]])],
    ],
    ids=["no_areas", "empty", "point", "segment", "horizontal", "collinear"],
)
def test_is_inside_degenerate_areas_are_never_inside(area_list):
    assert _is_inside([0.5, 0.5], area_list) is False


def test_is_inside_closed_polygon_with_repeated_first_vertex():
    closed = Area("closed", SQUARE.vertex_list + [SQUARE.vertex_list[0]])
    assert _is_inside([0.5, 0.5], [closed]) is True
    assert _is_inside([1.5, 0.5], [closed]) is False


def test_is_inside_does_not_mutate_inputs():
    vertices = [list(v) for v in SQUARE.vertex_list]
    area = Area("copy", vertices)
    location = [0.5, 0.5]
    _is_inside(location, [area])
    assert vertices == SQUARE.vertex_list
    assert location == [0.5, 0.5]


@pytest.mark.parametrize("location", [[], [0.5], [0.5, 0.5, 0.5]])
def test_is_inside_wrong_location_length_raises_value_error(location):
    with pytest.raises(ValueError):
        _is_inside(location, [SQUARE])


@pytest.mark.parametrize("location", [None, 1.0])
def test_is_inside_non_iterable_location_raises_type_error(location):
    with pytest.raises(TypeError):
        _is_inside(location, [SQUARE])


def test_is_inside_none_area_list_raises_type_error():
    with pytest.raises(TypeError):
        _is_inside([0.5, 0.5], None)


def test_is_inside_malformed_vertex_raises_value_error():
    with pytest.raises(ValueError):
        _is_inside([0.5, 0.5], [Area("bad", [[0, 0], [1], [1, 1]])])


def test_is_inside_non_numeric_coordinate_raises_type_error():
    with pytest.raises(TypeError):
        _is_inside(["a", 0.5], [SQUARE])


def test_is_inside_non_area_item_raises_attribute_error():
    with pytest.raises(AttributeError):
        _is_inside([0.5, 0.5], [[[0, 0], [1, 0], [1, 1]]])
