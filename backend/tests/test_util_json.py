# SPDX-License-Identifier: Apache-2.0
"""Unit tests for src.util.json (CustomJSONEncoder and dumps)."""

import collections
import dataclasses
import json
from datetime import date, datetime, timedelta, timezone

import pytest

import src.util
from src.util import json as util_json
from src.util.json import CustomJSONEncoder, dumps
from src.util.status import State, Status


@dataclasses.dataclass
class Point:
    x: int
    y: int


@dataclasses.dataclass
class Wrapper:
    point: Point
    stamp: datetime
    tags: set


@dataclasses.dataclass
class Empty:
    pass


class Opaque:
    """A plain object without __iter__ and not a dataclass."""


def test_package_exposes_json_module():
    assert src.util.json is util_json


@pytest.mark.parametrize(
    "obj, expected",
    [
        (None, "null"),
        (True, "true"),
        (0, "0"),
        (-1.5, "-1.5"),
        ("", '""'),
        ("abc", '"abc"'),
        ([], "[]"),
        ({}, "{}"),
        ([1, "a", None], '[1, "a", null]'),
        ({"a": [1, {"b": None}]}, '{"a": [1, {"b": null}]}'),
        ((1, 2), "[1, 2]"),
    ],
)
def test_dumps_native_types_match_stdlib(obj, expected):
    assert dumps(obj) == expected == json.dumps(obj)


def test_dumps_dataclass_uses_fields():
    assert json.loads(dumps(Point(1, 2))) == {"x": 1, "y": 2}


def test_dumps_empty_dataclass():
    assert dumps(Empty()) == "{}"


def test_dumps_nested_dataclass_with_datetime_and_set():
    stamp = datetime(2026, 1, 2, 3, 4, 5)
    result = json.loads(dumps(Wrapper(Point(0, -1), stamp, {"only"})))
    assert result == {
        "point": {"x": 0, "y": -1},
        "stamp": "2026-01-02T03:04:05",
        "tags": ["only"],
    }


def test_dumps_status_dataclass_with_int_enum():
    status = Status("robot_1", State.ACTIVE, [35.0, 137.0], info=["i"], node="robot.dummy")
    assert json.loads(dumps(status)) == {
        "name": "robot_1",
        "state": 3,
        "location": [35.0, 137.0],
        "info": ["i"],
        "detail": [],
        "command": [],
        "node": "robot.dummy",
    }


@pytest.mark.parametrize(
    "value, expected",
    [
        (datetime(2026, 1, 2, 3, 4, 5), "2026-01-02T03:04:05"),
        (datetime(2026, 1, 2, 3, 4, 5, 678000), "2026-01-02T03:04:05.678000"),
        (datetime(2026, 1, 2, tzinfo=timezone(timedelta(hours=9))), "2026-01-02T00:00:00+09:00"),
        (datetime(2026, 1, 2, tzinfo=timezone.utc), "2026-01-02T00:00:00+00:00"),
        (date(2026, 12, 31), "2026-12-31"),
        (date.min, "0001-01-01"),
    ],
)
def test_dumps_datetime_and_date_as_isoformat(value, expected):
    assert dumps(value) == json.dumps(expected)
    assert dumps({"t": value}) == json.dumps({"t": expected})


@pytest.mark.parametrize(
    "value, expected",
    [
        (set(), []),
        ({7}, [7]),
        (frozenset({"a"}), ["a"]),
        (range(3), [0, 1, 2]),
        ((i * 2 for i in range(3)), [0, 2, 4]),
        (iter([]), []),
        (collections.deque([1, 2]), [1, 2]),
        (b"ab", [97, 98]),
        ({"a": 1}.keys(), ["a"]),
        ({"a": 1}.values(), [1]),
    ],
)
def test_dumps_iterables_as_list(value, expected):
    assert json.loads(dumps(value)) == expected


def test_dumps_sorted_set_output_is_deterministic_when_sorted_first():
    assert dumps(sorted({3, 1, 2})) == "[1, 2, 3]"


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({"sort_keys": True}, '{"a": 2, "b": 1}'),
        ({"separators": (",", ":")}, '{"b":1,"a":2}'),
        ({"indent": 2}, '{\n  "b": 1,\n  "a": 2\n}'),
    ],
)
def test_dumps_forwards_kwargs(kwargs, expected):
    assert dumps({"b": 1, "a": 2}, **kwargs) == expected


@pytest.mark.parametrize("ensure_ascii, expected", [(True, '"\\u5f85\\u6a5f"'), (False, '"\u5f85\u6a5f"')])
def test_dumps_ensure_ascii(ensure_ascii, expected):
    assert dumps("\u5f85\u6a5f", ensure_ascii=ensure_ascii) == expected


def test_dumps_default_ensure_ascii_matches_stdlib():
    assert dumps("\u5f85\u6a5f") == json.dumps("\u5f85\u6a5f")


def test_dumps_rejects_duplicate_cls_kwarg():
    with pytest.raises(TypeError):
        dumps({}, cls=json.JSONEncoder)


@pytest.mark.parametrize("value", [Opaque(), object(), 1 + 2j, timedelta(seconds=1)])
def test_dumps_unsupported_type_raises_type_error(value):
    with pytest.raises(TypeError, match="not JSON serializable"):
        dumps(value)


def test_dumps_unsupported_type_nested_in_dataclass_raises_type_error():
    with pytest.raises(TypeError):
        dumps(Point(Opaque(), 1))


def test_dumps_non_string_dict_key_raises_type_error():
    with pytest.raises(TypeError):
        dumps({datetime(2026, 1, 1): 1})


def test_dumps_circular_reference_raises_value_error():
    data = []
    data.append(data)
    with pytest.raises(ValueError, match="Circular reference"):
        dumps(data)


def test_dumps_circular_reference_through_default_raises_value_error():
    @dataclasses.dataclass
    class Node:
        child: object = None

    node = Node()
    node.child = node
    with pytest.raises(ValueError, match="Circular reference"):
        dumps(node)


def test_encoder_default_directly():
    encoder = CustomJSONEncoder()
    assert encoder.default(Point(1, 2)) == {"x": 1, "y": 2}
    assert encoder.default({1, 2}) == [1, 2]
    assert encoder.default(date(2026, 1, 1)) == "2026-01-01"
    with pytest.raises(TypeError):
        encoder.default(Opaque())


def test_encoder_usable_with_stdlib_json_dumps():
    assert json.dumps({"p": Point(1, 2)}, cls=CustomJSONEncoder) == '{"p": {"x": 1, "y": 2}}'


@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="CustomJSONEncoder.default uses o.__dict__, which slotted dataclasses do not have",
)
def test_dumps_slotted_dataclass():
    @dataclasses.dataclass(slots=True)
    class Slotted:
        a: int = 1

    assert json.loads(dumps(Slotted())) == {"a": 1}


@pytest.mark.xfail(
    strict=True,
    reason="Non-dict Mappings hit the generic __iter__ branch and serialize as a list of keys",
)
def test_dumps_non_dict_mapping_serializes_as_object():
    assert json.loads(dumps(collections.UserDict(a=1))) == {"a": 1}


@pytest.mark.xfail(
    strict=True,
    reason="dataclasses.is_dataclass() is also true for dataclass types; the class __dict__ "
    "(mappingproxy) is then serialized as a list of attribute names instead of raising TypeError",
)
def test_dumps_dataclass_type_raises_type_error():
    with pytest.raises(TypeError):
        dumps(Point)
