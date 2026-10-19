import dataclasses
import json
from datetime import date, datetime, timezone

import pytest

from src.util import json as ujson
from src.util.status import State, Status


@dataclasses.dataclass
class Point:
    x: int
    y: int


@dataclasses.dataclass
class Wrapper:
    name: str
    point: Point
    tags: set


def test_native_types_pass_through_unchanged():
    obj = {"a": 1, "b": [1.5, "x", None, True], "c": {"d": (1, 2)}}
    assert ujson.dumps(obj) == json.dumps(obj)


def test_kwargs_are_forwarded_to_json_dumps():
    assert ujson.dumps({"b": 1, "a": "あ"}, sort_keys=True, ensure_ascii=False) == '{"a": "あ", "b": 1}'
    assert ujson.dumps([1, 2], separators=(",", ":")) == "[1,2]"


def test_dataclass_instance_is_encoded_as_dict():
    assert json.loads(ujson.dumps(Point(1, 2))) == {"x": 1, "y": 2}


def test_nested_dataclass_and_set_are_encoded_recursively():
    out = json.loads(ujson.dumps(Wrapper("w", Point(3, 4), {7})))
    assert out == {"name": "w", "point": {"x": 3, "y": 4}, "tags": [7]}


def test_status_dataclass_round_trip():
    status = Status(name="amr1", state=State.ACTIVE, location=[35.0, 137.0], info=["i"], node="robot.dummy")
    out = json.loads(ujson.dumps(status))
    assert out == {
        "name": "amr1",
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
        ({3}, [3]),
        (frozenset({"a"}), ["a"]),
        ((i * 2 for i in range(3)), [0, 2, 4]),
        (range(3), [0, 1, 2]),
        ({"k": 1}.keys(), ["k"]),
    ],
)
def test_iterables_are_encoded_as_lists(value, expected):
    assert json.loads(ujson.dumps(value)) == expected


def test_datetime_is_encoded_as_isoformat():
    dt = datetime(2026, 1, 2, 3, 4, 5, 6000, tzinfo=timezone.utc)
    assert json.loads(ujson.dumps({"t": dt})) == {"t": "2026-01-02T03:04:05.006000+00:00"}


def test_naive_datetime_is_encoded_as_isoformat():
    assert ujson.dumps(datetime(2026, 1, 2, 3, 4, 5)) == '"2026-01-02T03:04:05"'


def test_date_is_encoded_as_isoformat():
    assert ujson.dumps(date(2026, 12, 31)) == '"2026-12-31"'


def test_int_enum_is_encoded_as_its_value():
    assert ujson.dumps([State.ERROR, State.HIDE]) == "[5, -1]"


def test_unsupported_type_raises_type_error():
    with pytest.raises(TypeError):
        ujson.dumps(object())


def test_encoder_class_is_usable_directly():
    assert json.dumps({"s": {1}}, cls=ujson.CustomJSONEncoder) == '{"s": [1]}'


def test_bytes_are_encoded_as_list_of_ints():
    # Documents current behaviour: bytes fall into the generic __iter__ branch.
    assert ujson.dumps(b"AB") == "[65, 66]"


@pytest.mark.xfail(strict=True, raises=AttributeError, reason="BUG: slots dataclasses have no __dict__")
def test_slots_dataclass_is_encoded_as_dict():
    @dataclasses.dataclass(slots=True)
    class Slotted:
        a: int

    assert json.loads(ujson.dumps(Slotted(1))) == {"a": 1}


@pytest.mark.xfail(strict=True, reason="BUG: is_dataclass() is True for the class itself, so the class __dict__ is encoded")
def test_dataclass_type_is_rejected():
    with pytest.raises(TypeError):
        ujson.dumps(Point)
