import pytest

from src.util.map import Area, _is_inside

SQUARE = Area(name="square", vertex_list=[[0.0, 0.0], [0.0, 10.0], [10.0, 10.0], [10.0, 0.0]])
SQUARE_CCW = Area(name="square_ccw", vertex_list=list(reversed(SQUARE.vertex_list)))
FAR_SQUARE = Area(name="far", vertex_list=[[20.0, 20.0], [20.0, 30.0], [30.0, 30.0], [30.0, 20.0]])
# U shape: square 0..10 with the notch x in (3,7), y in (5,10] removed.
U_SHAPE = Area(
    name="u",
    vertex_list=[[0, 0], [10, 0], [10, 10], [7, 10], [7, 5], [3, 5], [3, 10], [0, 10]],
)
TRIANGLE = Area(name="tri", vertex_list=[[0, 0], [10, 0], [5, 10]])


def test_area_fields():
    a = Area(name="a", vertex_list=[[1, 2]])
    assert a.name == "a" and a.vertex_list == [[1, 2]]
    assert Area(**{"name": "a", "vertex_list": [[1, 2]]}) == a


@pytest.mark.parametrize("area", [SQUARE, SQUARE_CCW])
@pytest.mark.parametrize("point", [[5, 5], [0.1, 0.1], [9.9, 9.9], [1, 9]])
def test_point_inside_square_either_winding(area, point):
    assert _is_inside(point, [area]) is True


@pytest.mark.parametrize("area", [SQUARE, SQUARE_CCW])
@pytest.mark.parametrize("point", [[-1, 5], [11, 5], [5, -1], [5, 11], [-1, -1], [100, 100]])
def test_point_outside_square_either_winding(area, point):
    assert _is_inside(point, [area]) is False


def test_concave_polygon():
    assert _is_inside([1, 8], [U_SHAPE]) is True
    assert _is_inside([8, 8], [U_SHAPE]) is True
    assert _is_inside([5, 2], [U_SHAPE]) is True
    assert _is_inside([5, 8], [U_SHAPE]) is False  # inside the notch


def test_triangle():
    assert _is_inside([5, 5], [TRIANGLE]) is True
    assert _is_inside([1, 8], [TRIANGLE]) is False


def test_empty_area_list_is_outside():
    assert _is_inside([5, 5], []) is False


def test_area_without_vertices_is_outside():
    assert _is_inside([5, 5], [Area(name="empty", vertex_list=[])]) is False


def test_degenerate_area_does_not_divide_by_zero():
    line = Area(name="line", vertex_list=[[0, 5], [10, 5]])
    assert _is_inside([5, 5], [line]) is False
    assert _is_inside([5, 4], [line]) is False


@pytest.mark.parametrize("areas", [[SQUARE, FAR_SQUARE], [FAR_SQUARE, SQUARE]])
def test_multiple_areas_any_match(areas):
    assert _is_inside([5, 5], areas) is True
    assert _is_inside([25, 25], areas) is True
    assert _is_inside([15, 15], areas) is False


def test_overlapping_areas_do_not_cancel_out():
    shifted = Area(name="shifted", vertex_list=[[5, 5], [5, 15], [15, 15], [15, 5]])
    assert _is_inside([7, 7], [SQUARE, shifted]) is True
    assert _is_inside([12, 12], [SQUARE, shifted]) is True


def test_outside_area_before_inside_area_still_detected():
    assert _is_inside([25, 25], [SQUARE, U_SHAPE, TRIANGLE, FAR_SQUARE]) is True


def test_accepts_tuple_location_and_real_coordinates():
    # Lat/lng-sized coordinates as used by robot locations.
    yard = Area(
        name="yard",
        vertex_list=[[35.0500, 137.1500], [35.0500, 137.1600], [35.0600, 137.1600], [35.0600, 137.1500]],
    )
    assert _is_inside((35.0550, 137.1550), [yard]) is True
    assert _is_inside((35.0450, 137.1550), [yard]) is False
