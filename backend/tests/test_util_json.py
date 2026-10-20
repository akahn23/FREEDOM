import collections
import dataclasses
import json
from datetime import date, datetime, timedelta, timezone

import pytest
from aiohttp import web

from src.util.json import CustomJSONEncoder, dumps


@dataclasses.dataclass
class Point:
    x: int
    y: int


@dataclasses.dataclass
class Shape:
    name: str
    points: list[Point]
    created: datetime


@dataclasses.dataclass(slots=True)
class SlotPoint:
    x: int
    y: int


def encode(o):
    return CustomJSONEncoder().default(o)


def test_dataclass_is_encoded_as_its_dict():
    assert encode(Point(1, 2)) == {"x": 1, "y": 2}
    assert dumps(Point(1, 2)) == '{"x": 1, "y": 2}'


def test_nested_dataclasses_and_datetimes():
    created = datetime(2026, 1, 2, 3, 4, 5)
    shape = Shape("tri", [Point(0, 0), Point(1, 1)], created)
    assert json.loads(dumps(shape)) == {
        "name": "tri",
        "points": [{"x": 0, "y": 0}, {"x": 1, "y": 1}],
        "created": "2026-01-02T03:04:05",
    }


@pytest.mark.parametrize("value, expected", [
    ({3}, [3]),
    (frozenset({"a"}), ["a"]),
    (range(3), [0, 1, 2]),
    ((i * 2 for i in range(3)), [0, 2, 4]),
    (iter([1, 2]), [1, 2]),
    (collections.deque([1, 2]), [1, 2]),
    (b"ab", [97, 98]),
])
def test_iterables_are_encoded_as_lists(value, expected):
    assert encode(value) == expected


def test_set_inside_container_is_encoded_via_dumps():
    assert json.loads(dumps({"ids": {1}})) == {"ids": [1]}


def test_user_list_subclass_is_encoded_as_list():
    assert dumps(collections.UserList([1, 2])) == "[1, 2]"


def test_datetime_isoformat():
    assert encode(datetime(2026, 10, 20, 1, 2, 3)) == "2026-10-20T01:02:03"


def test_aware_datetime_isoformat_keeps_offset():
    dt = datetime(2026, 10, 20, 1, 2, 3, tzinfo=timezone(timedelta(hours=9)))
    assert encode(dt) == "2026-10-20T01:02:03+09:00"


def test_date_isoformat():
    assert encode(date(2026, 10, 20)) == "2026-10-20"


def test_native_types_bypass_default():
    assert dumps({"a": [1, 2.5, "x", None, True]}) == '{"a": [1, 2.5, "x", null, true]}'


@pytest.mark.parametrize("value", [object(), 1 + 2j, timedelta(seconds=1)])
def test_unsupported_type_falls_back_to_default_type_error(value):
    with pytest.raises(TypeError, match="not JSON serializable"):
        encode(value)
    with pytest.raises(TypeError):
        dumps(value)


def test_dumps_forwards_kwargs():
    assert dumps({"b": 1, "a": "日本"}, sort_keys=True, ensure_ascii=False) == '{"a": "日本", "b": 1}'
    assert dumps([1], indent=2) == "[\n  1\n]"


@pytest.mark.xfail(strict=True, raises=AttributeError,
                   reason="Finding: default() uses o.__dict__, which slots=True dataclasses do not have; "
                          "dataclasses.asdict() would work")
def test_slots_dataclass_is_encoded():
    assert dumps(SlotPoint(1, 2)) == '{"x": 1, "y": 2}'


@pytest.mark.xfail(strict=True,
                   reason="Finding: non-dict Mappings hit the __iter__ branch and are encoded as a list of keys, "
                          "silently dropping values")
def test_non_dict_mapping_keeps_values():
    assert json.loads(dumps(collections.UserDict({"a": 1}))) == {"a": 1}


async def test_aiohttp_json_response_with_custom_dumps(aiohttp_client):
    async def handler(request):
        return web.json_response(
            [Point(1, 2), {"when": date(2026, 1, 1), "tags": {"x"}}], dumps=dumps)

    app = web.Application()
    app.router.add_get("/", handler)
    client = await aiohttp_client(app)
    resp = await client.get("/")
    assert resp.status == 200
    assert await resp.json() == [{"x": 1, "y": 2}, {"when": "2026-01-01", "tags": ["x"]}]
