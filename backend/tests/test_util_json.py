# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from src import util


@dataclasses.dataclass
class Point:
    x: int
    y: int


def roundtrip(obj, **kwargs):
    return json.loads(util.json.dumps(obj, **kwargs))


def test_plain_json_types_are_unchanged():
    obj = {"a": 1, "b": [1.5, "x", None, True]}
    assert util.json.dumps(obj) == json.dumps(obj)


def test_dataclass_is_serialised_as_its_dict():
    assert roundtrip(Point(1, 2)) == {"x": 1, "y": 2}


def test_nested_dataclasses():
    @dataclasses.dataclass
    class Line:
        start: Point
        end: Point

    assert roundtrip(Line(Point(0, 0), Point(3, 4))) == {"start": {"x": 0, "y": 0}, "end": {"x": 3, "y": 4}}


def test_dataclass_instance_attributes_are_included():
    p = Point(1, 2)
    p.extra = "runtime"
    assert roundtrip(p) == {"x": 1, "y": 2, "extra": "runtime"}


def test_set_and_tuple_and_generator_become_lists():
    assert sorted(roundtrip({3, 1, 2})) == [1, 2, 3]
    assert roundtrip((1, 2)) == [1, 2]
    assert roundtrip(i * 2 for i in range(3)) == [0, 2, 4]
    assert roundtrip(frozenset({"a"})) == ["a"]


def test_datetime_and_date_use_isoformat():
    dt = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert roundtrip({"dt": dt, "d": date(2026, 1, 2)}) == {"dt": "2026-01-02T03:04:05+00:00", "d": "2026-01-02"}


def test_state_enum_serialises_as_int():
    assert roundtrip(util.status.State.ERROR) == 5


def test_status_dataclass_serialises():
    status = util.status.Status("amr_1", util.status.State.ACTIVE, [35.0, 137.0], info=["ok"])
    assert roundtrip(status) == {
        "name": "amr_1", "state": 3, "location": [35.0, 137.0],
        "info": ["ok"], "detail": [], "command": [], "node": "",
    }


def test_unsupported_type_raises_type_error():
    with pytest.raises(TypeError):
        util.json.dumps(timedelta(seconds=1))
    with pytest.raises(TypeError):
        util.json.dumps(object())


def test_kwargs_are_forwarded_to_json_dumps():
    assert util.json.dumps({"b": 1, "a": "あ"}, sort_keys=True, ensure_ascii=False) == '{"a": "あ", "b": 1}'
    assert util.json.dumps([1], indent=2) == "[\n  1\n]"
