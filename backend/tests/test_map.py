import util.map
from util.map import Area, _is_inside


SQUARE = Area(name="square", vertex_list=[[0, 0], [0, 10], [10, 10], [10, 0]])


def test_area_fields():
    assert SQUARE.name == "square"
    assert SQUARE.vertex_list == [[0, 0], [0, 10], [10, 10], [10, 0]]
    assert isinstance(SQUARE, util.map.Area)


def test_point_inside_square():
    assert _is_inside([5, 5], [SQUARE]) is True
    assert _is_inside([1, 9], [SQUARE]) is True


def test_point_outside_square():
    assert _is_inside([15, 5], [SQUARE]) is False
    assert _is_inside([-5, 5], [SQUARE]) is False
    assert _is_inside([5, 15], [SQUARE]) is False
    assert _is_inside([5, -5], [SQUARE]) is False


def test_multiple_areas_and_empty_list():
    far = Area(name="far", vertex_list=[[20, 20], [20, 30], [30, 30], [30, 20]])
    assert _is_inside([25, 25], [SQUARE, far]) is True
    assert _is_inside([15, 15], [SQUARE, far]) is False
    assert _is_inside([5, 5], []) is False
