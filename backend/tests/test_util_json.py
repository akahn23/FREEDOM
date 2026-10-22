# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from src.util.json import CustomJSONEncoder, dumps


@dataclasses.dataclass
class Point:
    x: int
    y: int


@dataclasses.dataclass
class Event:
    name: str
    at: datetime
    point: Point
    tags: set


def test_dataclass_serializes_to_field_dict():
    assert json.loads(dumps(Point(x=1, y=2))) == {"x": 1, "y": 2}


def test_nested_dataclass_with_custom_fields():
    at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    event = Event(name="arrive", at=at, point=Point(x=3, y=4), tags={"amr"})
    assert json.loads(dumps(event)) == {
        "name": "arrive",
        "at": "2026-01-02T03:04:05+00:00",
        "point": {"x": 3, "y": 4},
        "tags": ["amr"],
    }


@pytest.mark.parametrize(
    "value",
    [
        datetime(2026, 1, 2, 3, 4, 5, 678000, tzinfo=timezone.utc),
        datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=9))),
        date(2026, 12, 31),
    ],
)
def test_datetime_and_date_serialize_to_isoformat(value):
    assert dumps(value) == json.dumps(value.isoformat())


def test_set_serializes_to_array():
    assert sorted(json.loads(dumps({3, 1, 2}))) == [1, 2, 3]


def test_generator_serializes_to_array():
    assert json.loads(dumps(i * i for i in range(4))) == [0, 1, 4, 9]


def test_iterable_inside_container():
    assert json.loads(dumps({"ids": frozenset([7]), "range": range(3)})) == {"ids": [7], "range": [0, 1, 2]}


@pytest.mark.parametrize(
    "value",
    [
        {"a": 1, "b": [1, 2.5, None, True], "c": {"d": "e"}},
        [1, "two", {"three": 3}, []],
        "\u65e5\u672c\u8a9e",
        42,
        None,
    ],
)
def test_plain_json_values_round_trip(value):
    assert json.loads(dumps(value)) == value
    assert dumps(value) == json.dumps(value)


def test_kwargs_are_forwarded():
    assert dumps({"b": 1, "a": 2}, sort_keys=True, separators=(",", ":")) == '{"a":2,"b":1}'


def test_encoder_class_can_be_used_directly():
    assert json.dumps([Point(x=0, y=0)], cls=CustomJSONEncoder) == '[{"x": 0, "y": 0}]'


def test_unsupported_type_raises_type_error():
    with pytest.raises(TypeError):
        dumps(object())
