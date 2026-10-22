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
class Named:
    name: str
    point: Point
    tags: list[str] = dataclasses.field(default_factory=list)


def test_dataclass_serializes_to_field_dict():
    assert json.loads(dumps(Point(1, 2))) == {'x': 1, 'y': 2}


def test_nested_dataclass_serializes_recursively():
    obj = Named(name='a', point=Point(3, 4), tags=['t'])
    assert json.loads(dumps(obj)) == {'name': 'a', 'point': {'x': 3, 'y': 4}, 'tags': ['t']}


def test_set_serializes_to_array():
    assert sorted(json.loads(dumps({3, 1, 2}))) == [1, 2, 3]
    assert json.loads(dumps(frozenset({'a'}))) == ['a']


def test_generator_serializes_to_array():
    assert json.loads(dumps(i * 2 for i in range(3))) == [0, 2, 4]


def test_other_iterables_serialize_to_array():
    assert json.loads(dumps(range(3))) == [0, 1, 2]
    assert json.loads(dumps({'k': iter(['a', 'b'])})) == {'k': ['a', 'b']}


def test_datetime_serializes_to_iso8601():
    dt = datetime(2024, 3, 5, 16, 4, 5, 123000, tzinfo=timezone.utc)
    assert json.loads(dumps(dt)) == '2024-03-05T16:04:05.123000+00:00'
    assert datetime.fromisoformat(json.loads(dumps(dt))) == dt


def test_datetime_with_offset_keeps_offset():
    dt = datetime(2024, 3, 5, 9, 0, tzinfo=timezone(timedelta(hours=9)))
    assert json.loads(dumps(dt)) == '2024-03-05T09:00:00+09:00'


def test_date_serializes_to_iso8601():
    assert json.loads(dumps(date(2024, 3, 5))) == '2024-03-05'


def test_plain_dict_serializes_normally():
    obj = {'a': 1, 'b': [True, None], 'c': {'d': 'e'}, 'f': 1.5}
    assert dumps(obj) == json.dumps(obj)
    assert json.loads(dumps(obj)) == obj


def test_mixed_structure():
    obj = {'when': date(2024, 1, 2), 'ids': {7}, 'p': Point(0, 1)}
    assert json.loads(dumps(obj)) == {'when': '2024-01-02', 'ids': [7], 'p': {'x': 0, 'y': 1}}


def test_kwargs_are_forwarded_to_json_dumps():
    assert dumps({'b': 1, 'a': 2}, sort_keys=True) == '{"a": 2, "b": 1}'
    assert dumps([1], indent=2) == '[\n  1\n]'
    assert dumps({'k': '\u65e5'}, ensure_ascii=False) == '{"k": "\u65e5"}'


def test_encoder_usable_directly_with_json_dumps():
    assert json.loads(json.dumps({'s': {1}}, cls=CustomJSONEncoder)) == {'s': [1]}


def test_encoder_default_returns_python_values():
    encoder = CustomJSONEncoder()
    assert encoder.default(Point(1, 2)) == {'x': 1, 'y': 2}
    assert encoder.default({1}) == [1]
    assert encoder.default(date(2024, 3, 5)) == '2024-03-05'


def test_unsupported_type_raises_type_error():
    with pytest.raises(TypeError):
        dumps(object())
    with pytest.raises(TypeError):
        dumps(1 + 2j)
