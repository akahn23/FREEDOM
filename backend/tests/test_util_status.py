import dataclasses

import pytest

from src.util.status import State, Status


def test_state_values_match_layer_order():
    assert {s.name: s.value for s in State} == {
        "HIDE": -1,
        "DISCONNECT": 0,
        "WAITING": 1,
        "MANUAL": 2,
        "ACTIVE": 3,
        "WARNING": 4,
        "ERROR": 5,
    }


def test_state_is_ordered_by_severity():
    assert sorted(State, reverse=True)[0] is State.ERROR
    assert State.HIDE < State.DISCONNECT < State.WAITING < State.MANUAL < State.ACTIVE < State.WARNING < State.ERROR
    assert max(State.WARNING, State.ACTIVE) is State.WARNING


@pytest.mark.parametrize("value", range(-1, 6))
def test_state_constructible_from_int(value):
    assert State(value) == value
    assert isinstance(State(value), int)


def test_state_rejects_unknown_int():
    with pytest.raises(ValueError):
        State(6)


def test_status_defaults():
    s = Status(name="n")
    assert s.state is State.HIDE
    assert s.location is None
    assert s.info == [] and s.detail == [] and s.command == []
    assert s.node == ""


def test_status_requires_name():
    with pytest.raises(TypeError):
        Status()


def test_status_list_defaults_are_not_shared():
    a, b = Status(name="a"), Status(name="b")
    a.info.append("x")
    a.detail.append("y")
    a.command.append({"z": 1})
    assert b.info == [] and b.detail == [] and b.command == []


def test_status_positional_field_order():
    s = Status("n", State.ERROR, [1.0, 2.0], ["i"], ["d"], [{"c": 1}], "robot.dummy")
    assert dataclasses.astuple(s) == ("n", State.ERROR, [1.0, 2.0], ["i"], ["d"], [{"c": 1}], "robot.dummy")


def test_status_equality_and_asdict():
    s = Status(name="n", state=State.WARNING)
    assert s == Status(name="n", state=State.WARNING)
    assert s != Status(name="n", state=State.ERROR)
    assert dataclasses.asdict(s)["state"] == 4
