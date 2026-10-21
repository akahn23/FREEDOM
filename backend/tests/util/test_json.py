# SPDX-License-Identifier: Apache-2.0

import dataclasses
import decimal
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from src.util.json import CustomJSONEncoder, dumps


@dataclasses.dataclass
class Point:
    x: int
    y: int


@dataclasses.dataclass
class Robot:
    name: str
    location: Point
    tags: list = dataclasses.field(default_factory=list)


class Countdown:
    """A custom iterable that is neither a list nor a dataclass."""

    def __init__(self, start):
        self.start = start

    def __iter__(self):
        return iter(range(self.start, 0, -1))


# (1) dataclass instances serialize to their __dict__

def test_dataclass_serializes_to_its_dict():
    point = Point(1, 2)
    assert json.loads(dumps(point)) == point.__dict__ == {"x": 1, "y": 2}


def test_nested_dataclass_serializes_recursively():
    robot = Robot("amr_1", Point(3, 4), tags=["a", "b"])
    assert json.loads(dumps(robot)) == {
        "name": "amr_1",
        "location": {"x": 3, "y": 4},
        "tags": ["a", "b"],
    }


def test_encoder_default_returns_dict_for_dataclass():
    point = Point(5, 6)
    assert CustomJSONEncoder().default(point) == {"x": 5, "y": 6}


# (2) iterable objects serialize to lists

def test_generator_serializes_to_list():
    assert json.loads(dumps(i * i for i in range(4))) == [0, 1, 4, 9]


def test_set_serializes_to_list():
    assert sorted(json.loads(dumps({3, 1, 2}))) == [1, 2, 3]


def test_frozenset_serializes_to_list():
    assert json.loads(dumps(frozenset(["only"]))) == ["only"]


def test_custom_iterable_serializes_to_list():
    assert json.loads(dumps(Countdown(3))) == [3, 2, 1]


def test_encoder_default_returns_list_for_iterable():
    result = CustomJSONEncoder().default({"a"})
    assert result == ["a"]
    assert isinstance(result, list)


def test_iterable_items_are_encoded_recursively():
    payload = {"points": (Point(i, i) for i in range(2))}
    assert json.loads(dumps(payload)) == {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 1}]}


# (3) datetime and date serialize to ISO format strings

def test_naive_datetime_serializes_to_isoformat():
    value = datetime(2026, 10, 21, 13, 5, 30, 123456)  # noqa: DTZ001
    assert dumps(value) == '"2026-10-21T13:05:30.123456"'


def test_aware_datetime_keeps_utc_offset():
    value = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=9)))
    assert json.loads(dumps(value)) == "2026-01-02T03:04:05+09:00"


def test_date_serializes_to_isoformat():
    assert dumps(date(2026, 10, 21)) == '"2026-10-21"'


def test_datetimes_inside_containers():
    payload = {"start": datetime(2026, 1, 1, 0, 0), "days": [date(2026, 1, 1), date(2026, 1, 2)]}  # noqa: DTZ001
    assert json.loads(dumps(payload)) == {
        "start": "2026-01-01T00:00:00",
        "days": ["2026-01-01", "2026-01-02"],
    }


# (4) plain JSON types round-trip normally

@pytest.mark.parametrize(
    "value",
    [
        {"a": 1, "b": [1, 2, 3], "c": {"d": None, "e": True}},
        [1, "two", 3.5, None, False, [], {}],
        "hello",
        "",
        0,
        -1.25,
        None,
        True,
    ],
)
def test_plain_values_round_trip(value):
    assert json.loads(dumps(value)) == value


def test_plain_values_match_standard_json_dumps():
    payload = {"name": "lamp_1", "status": [0, 1, 2], "nested": {"ok": True}}
    assert dumps(payload) == json.dumps(payload)


def test_non_ascii_string_round_trips():
    text = "\u5f85\u6a5f"
    assert json.loads(dumps(text)) == text
    assert dumps(text, ensure_ascii=False) == '"' + text + '"'


def test_kwargs_are_forwarded_to_json_dumps():
    assert dumps({"b": 1, "a": 2}, sort_keys=True, indent=2) == '{\n  "a": 2,\n  "b": 1\n}'


def test_kwargs_cannot_override_encoder_class():
    with pytest.raises(TypeError):
        dumps({}, cls=json.JSONEncoder)


# (5) unsupported types raise TypeError via the base encoder

@pytest.mark.parametrize(
    "value",
    [object(), decimal.Decimal("1.5"), 1 + 2j, timedelta(seconds=1)],
    ids=["object", "decimal", "complex", "timedelta"],
)
def test_unsupported_type_raises_type_error(value):
    with pytest.raises(TypeError, match="is not JSON serializable"):
        dumps(value)


def test_encoder_default_delegates_to_base_for_unsupported_type():
    with pytest.raises(TypeError, match="Object of type object is not JSON serializable"):
        CustomJSONEncoder().default(object())


def test_unsupported_type_nested_in_container_raises_type_error():
    with pytest.raises(TypeError):
        dumps({"ok": 1, "bad": [object()]})
