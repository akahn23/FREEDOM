import itertools

import pytest

from src.util.map import Area, _is_inside


SQUARE = [[0, 0], [1, 0], [1, 1], [0, 1]]
# U shape: notch is (1, 1)-(2, 3)
U_SHAPE = [[0, 0], [3, 0], [3, 3], [2, 3], [2, 1], [1, 1], [1, 3], [0, 3]]
# L shape: horizontal edge (2, 1)-(1, 1) in the middle of the outline
L_SHAPE = [[0, 0], [2, 0], [2, 1], [1, 1], [1, 2], [0, 2]]
DIAMOND = [[1, 0], [2, 1], [1, 2], [0, 1]]
BOWTIE = [[0, 0], [2, 2], [2, 0], [0, 2]]


def inside(location, *vertex_lists):
    return _is_inside(location, [Area(f"area{i}", v) for i, v in enumerate(vertex_lists)])


def test_area_dataclass_fields():
    area = Area("zone", SQUARE)
    assert area.name == "zone"
    assert area.vertex_list is SQUARE


@pytest.mark.parametrize("point, expected", [
    ([0.5, 0.5], True),
    ([0.001, 0.999], True),
    ([2, 0.5], False),    # right of bounding box
    ([-1, 0.5], False),   # left of bounding box (ray crosses both sides)
    ([0.5, 2], False),    # above
    ([0.5, -1], False),   # below
    ([5, 5], False),
    ([-5, -5], False),
])
def test_square_interior_and_outside_bounding_box(point, expected):
    assert inside(point, SQUARE) is expected


@pytest.mark.parametrize("point, expected", [
    # Half-open convention: left/bottom edges are inside, right/top edges are outside.
    ([0, 0.5], True),
    ([0.5, 0], True),
    ([1, 0.5], False),
    ([0.5, 1], False),
])
def test_points_on_edges_follow_half_open_rule(point, expected):
    assert inside(point, SQUARE) is expected


@pytest.mark.parametrize("point, expected", [
    ([0, 0], True),
    ([1, 0], False),
    ([1, 1], False),
    ([0, 1], False),
])
def test_points_on_vertices(point, expected):
    assert inside(point, SQUARE) is expected


def test_shared_boundaries_of_tiling_belong_to_exactly_one_tile():
    tiles = [[[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1]] for x in (0, 1) for y in (0, 1)]
    for px, py in itertools.product([0, 0.5, 1, 1.5], repeat=2):
        hits = sum(inside([px, py], t) for t in tiles)
        assert hits == 1, (px, py)


@pytest.mark.parametrize("vertices", [SQUARE, SQUARE[::-1]], ids=["ccw", "cw"])
@pytest.mark.parametrize("point, expected", [
    ([0.5, 0.5], True), ([0, 0.5], True), ([1, 0.5], False), ([2, 2], False),
])
def test_winding_direction_does_not_matter(vertices, point, expected):
    assert inside(point, vertices) is expected


@pytest.mark.parametrize("point, expected", [
    ([0.5, 1], True),     # level with the horizontal edge, inside the left column
    ([1.5, 0.5], True),
    ([1.5, 1], False),    # on the horizontal edge (top edge -> outside)
    ([1.5, 1.5], False),  # in the missing quadrant
    ([2.5, 1], False),
    ([-1, 1], False),     # ray runs along the horizontal edge level
])
def test_horizontal_edges(point, expected):
    assert inside(point, L_SHAPE) is expected


def test_horizontal_edge_does_not_divide_by_zero():
    flat = [[0, 1], [5, 1], [5, 2], [0, 2]]
    assert inside([1, 1], flat) is True
    assert inside([1, 2], flat) is False


@pytest.mark.parametrize("point, expected", [
    ([0.5, 2], True),     # left arm
    ([2.5, 2], True),     # right arm
    ([1.5, 0.5], True),   # base
    ([1.5, 2], False),    # inside the notch
    ([1.5, 2.999], False),
    ([0.5, 1], True),     # ray crosses three edges
    ([-1, 1], False),     # ray crosses four edges
    ([1.5, 1], False),    # on notch floor (a top edge)
    ([1.5, 3], False),
])
def test_concave_polygon(point, expected):
    assert inside(point, U_SHAPE) is expected


@pytest.mark.parametrize("point, expected", [
    ([1, 1], True),
    ([1.5, 1], True),
    ([-1, 1], False),     # ray passes exactly through two vertices
    ([2.5, 1], False),
    ([1, 0], False),      # bottom vertex
    ([-1, 0], False),     # ray grazes the bottom vertex
    ([1, 2], False),      # top vertex
])
def test_ray_through_vertices(point, expected):
    assert inside(point, DIAMOND) is expected


def test_ray_through_non_extremal_vertex():
    triangle = [[0, 0], [2, 1], [0, 2]]
    assert inside([-1, 1], triangle) is False
    assert inside([1, 1], triangle) is True
    assert inside([3, 1], triangle) is False


@pytest.mark.parametrize("point, expected", [
    ([0.3, 1], True),
    ([1.7, 1], True),
    ([1, 0.3], False),
    ([1, 1.7], False),
])
def test_self_intersecting_polygon_uses_even_odd_rule(point, expected):
    assert inside(point, BOWTIE) is expected


@pytest.mark.parametrize("vertices", [
    [],
    [[0, 0]],
    [[0, 0], [1, 1]],
    [[0, 0], [0, 1], [0, 2]],
    [[0, 0], [1, 0], [2, 0]],
    [[0, 0], [1, 1], [2, 2]],
], ids=["empty", "single-vertex", "segment", "vertical-line", "horizontal-line", "diagonal-line"])
@pytest.mark.parametrize("point", [[0, 0], [0, 0.5], [0.5, 0.5], [1, 0], [1, 1]])
def test_degenerate_polygons_contain_nothing(vertices, point):
    assert inside(point, vertices) is False


def test_duplicate_and_closing_vertices_do_not_change_result():
    duplicated = [[0, 0], [1, 0], [1, 0], [1, 1], [0, 1], [0, 1]]
    closed = SQUARE + [SQUARE[0]]
    for point in ([0.5, 0.5], [0, 0.5], [1, 0.5], [2, 0.5], [-1, 0.5], [0.5, 0]):
        expected = inside(point, SQUARE)
        assert inside(point, duplicated) is expected
        assert inside(point, closed) is expected


def test_empty_area_list():
    assert _is_inside([0, 0], []) is False


def test_multiple_areas_any_match():
    far = [[10, 10], [11, 10], [11, 11], [10, 11]]
    assert inside([0.5, 0.5], SQUARE, far) is True
    assert inside([10.5, 10.5], SQUARE, far) is True
    assert inside([5, 5], SQUARE, far) is False


def test_overlapping_areas_do_not_cancel_out():
    shifted = [[0.5, 0], [1.5, 0], [1.5, 1], [0.5, 1]]
    assert inside([0.75, 0.5], SQUARE, shifted) is True
    assert inside([0.75, 0.5], SQUARE, SQUARE) is True


def test_outside_result_of_first_area_does_not_leak_into_second():
    concave_first = U_SHAPE
    assert inside([1.5, 2], concave_first, SQUARE) is False
    assert inside([0.5, 0.5], [[5, 5], [6, 5], [6, 6]], SQUARE) is True


def test_realistic_lat_lng_coordinates():
    lat, lng = 35.0834, 137.1563
    d = 0.0001
    area = [[lat, lng], [lat + d, lng], [lat + d, lng + d], [lat, lng + d]]
    assert inside([lat + d / 2, lng + d / 2], area) is True
    assert inside([lat + 2 * d, lng + d / 2], area) is False


def test_accepts_tuple_location_and_tuple_vertices():
    assert _is_inside((0.5, 0.5), [Area("t", [(0, 0), (1, 0), (1, 1), (0, 1)])]) is True


def test_malformed_location_raises():
    with pytest.raises(ValueError):
        _is_inside([0.5], [Area("a", SQUARE)])
