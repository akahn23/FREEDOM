import dataclasses
import json
from datetime import date, datetime, timezone

from util.json import CustomJSONEncoder, dumps


@dataclasses.dataclass
class Point:
    name: str
    x: int
    y: float


def test_dataclass_serializes_to_field_dict():
    result = json.loads(dumps(Point(name="p", x=1, y=2.5)))
    assert result == {"name": "p", "x": 1, "y": 2.5}


def test_nested_dataclass_in_container():
    result = json.loads(dumps({"points": [Point("a", 0, 0.0), Point("b", 1, 1.0)]}))
    assert result == {"points": [{"name": "a", "x": 0, "y": 0.0}, {"name": "b", "x": 1, "y": 1.0}]}


def test_set_serializes_to_array():
    result = json.loads(dumps({3, 1, 2}))
    assert isinstance(result, list)
    assert sorted(result) == [1, 2, 3]


def test_generator_serializes_to_array():
    result = json.loads(dumps(i * 2 for i in range(3)))
    assert result == [0, 2, 4]


def test_datetime_serializes_to_isoformat():
    dt = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert json.loads(dumps(dt)) == dt.isoformat() == "2026-01-02T03:04:05+00:00"


def test_date_serializes_to_isoformat():
    assert json.loads(dumps({"d": date(2026, 1, 2)})) == {"d": "2026-01-02"}


def test_encoder_usable_directly_and_kwargs_forwarded():
    assert json.loads(json.dumps(Point("p", 1, 2.0), cls=CustomJSONEncoder)) == {"name": "p", "x": 1, "y": 2.0}
    assert dumps({"b": 1, "a": 2}, sort_keys=True) == '{"a": 2, "b": 1}'
