import pytest

from src.util.map import Area, _is_inside

UNIT_SQUARE = Area(name='square', vertex_list=[[0, 0], [1, 0], [1, 1], [0, 1]])
FAR_SQUARE = Area(name='far', vertex_list=[[10, 10], [11, 10], [11, 11], [10, 11]])
OVERLAP_SQUARE = Area(name='overlap', vertex_list=[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5]])
# U shape: notch between x=1..2 above y=1
U_SHAPE = Area(name='u', vertex_list=[[0, 0], [3, 0], [3, 3], [2, 3], [2, 1], [1, 1], [1, 3], [0, 3]])


@pytest.mark.parametrize('point', [[0.5, 0.5], [0.1, 0.9], [0.999, 0.001]])
def test_point_inside_square(point):
    assert _is_inside(point, [UNIT_SQUARE]) is True


@pytest.mark.parametrize('point', [[1.5, 0.5], [-0.5, 0.5], [0.5, 1.5], [0.5, -0.5], [2, 2], [-1, -1]])
def test_point_outside_square(point):
    assert _is_inside(point, [UNIT_SQUARE]) is False


def test_vertex_order_does_not_matter():
    clockwise = Area(name='cw', vertex_list=list(reversed(UNIT_SQUARE.vertex_list)))
    assert _is_inside([0.5, 0.5], [clockwise]) is True
    assert _is_inside([1.5, 0.5], [clockwise]) is False


def test_empty_area_list_is_outside():
    assert _is_inside([0.5, 0.5], []) is False


def test_concave_polygon_even_crossings_is_outside():
    # Ray from the notch crosses two edges (x=2, x=3): even -> outside.
    assert _is_inside([1.5, 2], [U_SHAPE]) is False


def test_concave_polygon_odd_crossings_is_inside():
    # Ray from the left arm crosses three edges (x=1, x=2, x=3): odd -> inside.
    assert _is_inside([0.5, 2], [U_SHAPE]) is True
    assert _is_inside([1.5, 0.5], [U_SHAPE]) is True


def test_multiple_areas_inside_any():
    assert _is_inside([0.5, 0.5], [UNIT_SQUARE, FAR_SQUARE]) is True
    assert _is_inside([10.5, 10.5], [UNIT_SQUARE, FAR_SQUARE]) is True
    assert _is_inside([5, 5], [UNIT_SQUARE, FAR_SQUARE]) is False


def test_multiple_areas_order_independent():
    assert _is_inside([10.5, 10.5], [FAR_SQUARE, UNIT_SQUARE]) is True
    assert _is_inside([0.5, 0.5], [FAR_SQUARE, UNIT_SQUARE]) is True


def test_overlapping_areas_do_not_cancel_out():
    # Point in both squares: an even total crossing count across areas must not flip it back to outside.
    assert _is_inside([0.75, 0.75], [UNIT_SQUARE, OVERLAP_SQUARE]) is True
    assert _is_inside([0.75, 0.75], [OVERLAP_SQUARE, UNIT_SQUARE]) is True


def test_outside_first_area_does_not_leak_into_second():
    # Even crossings in the first area leave state False before checking the second.
    assert _is_inside([1.25, 1.25], [UNIT_SQUARE, OVERLAP_SQUARE]) is True
    assert _is_inside([-0.5, 0.5], [UNIT_SQUARE, OVERLAP_SQUARE]) is False


@pytest.mark.parametrize('point', [[1e-9, 0.5], [0.5, 1e-9], [1 - 1e-9, 0.5], [0.5, 1 - 1e-9]])
def test_points_just_inside_edges(point):
    assert _is_inside(point, [UNIT_SQUARE]) is True


@pytest.mark.parametrize('point', [[-1e-9, 0.5], [0.5, -1e-9], [1 + 1e-9, 0.5], [0.5, 1 + 1e-9]])
def test_points_just_outside_edges(point):
    assert _is_inside(point, [UNIT_SQUARE]) is False


# Ray casting here is half-open: points exactly on the left/bottom edges count as inside,
# points exactly on the right/top edges count as outside.
@pytest.mark.parametrize(('point', 'expected'), [
    ([0, 0.5], True),    # left edge
    ([0.5, 0], True),    # bottom edge
    ([1, 0.5], False),   # right edge
    ([0.5, 1], False),   # top edge
])
def test_points_exactly_on_edges(point, expected):
    assert _is_inside(point, [UNIT_SQUARE]) is expected


@pytest.mark.parametrize(('point', 'expected'), [
    ([0, 0], True),      # bottom-left
    ([1, 0], False),     # bottom-right
    ([1, 1], False),     # top-right
    ([0, 1], False),     # top-left
])
def test_points_exactly_on_vertices(point, expected):
    assert _is_inside(point, [UNIT_SQUARE]) is expected


def test_horizontal_edges_do_not_divide_by_zero():
    # Ray at the height of the horizontal bottom/top edges must skip them, not raise ZeroDivisionError.
    assert _is_inside([-1, 0], [UNIT_SQUARE]) is False
    assert _is_inside([-1, 1], [UNIT_SQUARE]) is False
