# SPDX-License-Identifier: Apache-2.0
"""Unit tests for src.util.status (State and Status)."""

import dataclasses
import enum

import pytest

import src.util
from src.util import status as util_status
from src.util.status import State, Status


def test_package_exposes_status_module():
    assert src.util.status is util_status


@pytest.mark.parametrize(
    "member, value",
    [
        (State.HIDE, -1),
        (State.DISCONNECT, 0),
        (State.WAITING, 1),
        (State.MANUAL, 2),
        (State.ACTIVE, 3),
        (State.WARNING, 4),
        (State.ERROR, 5),
    ],
)
def test_state_values(member, value):
    assert member.value == value
    assert member == value
    assert State(value) is member
    assert State[member.name] is member


def test_state_is_int_enum_with_exactly_seven_members():
    assert issubclass(State, enum.IntEnum)
    assert [m.name for m in State] == [
        "HIDE", "DISCONNECT", "WAITING", "MANUAL", "ACTIVE", "WARNING", "ERROR",
    ]


def test_state_order_is_layer_order():
    assert sorted(State, reverse=True)[0] is State.ERROR
    assert max(State) is State.ERROR
    assert min(State) is State.HIDE
    assert State.WARNING > State.ACTIVE > State.MANUAL > State.WAITING > State.DISCONNECT > State.HIDE


def test_state_supports_int_arithmetic_and_comparison():
    assert State.ACTIVE + 1 == State.WARNING
    assert int(State.ERROR) == 5
    assert State.WAITING < 2


@pytest.mark.parametrize("value", [-2, 6, 100, None, "ACTIVE", 3.5])
def test_state_invalid_value_raises_value_error(value):
    with pytest.raises(ValueError):
        State(value)


@pytest.mark.parametrize("name", ["active", "UNKNOWN", ""])
def test_state_invalid_name_raises_key_error(name):
    with pytest.raises(KeyError):
        State[name]


def test_status_defaults():
    status = Status("lamp_1")
    assert status.name == "lamp_1"
    assert status.state is State.HIDE
    assert status.location is None
    assert status.info == []
    assert status.detail == []
    assert status.command == []
    assert status.node == ""


def test_status_all_fields():
    command = [{"name": "on"}]
    status = Status("r", State.ERROR, [1.0, 2.0], ["i"], ["d"], command, "robot.dummy")
    assert dataclasses.astuple(status) == ("r", State.ERROR, [1.0, 2.0], ["i"], ["d"], command, "robot.dummy")


def test_status_field_order():
    assert [f.name for f in dataclasses.fields(Status)] == [
        "name", "state", "location", "info", "detail", "command", "node",
    ]


def test_status_name_is_required():
    with pytest.raises(TypeError):
        Status()


def test_status_rejects_unknown_kwarg():
    with pytest.raises(TypeError):
        Status("x", unknown=1)


def test_status_rejects_too_many_positional_args():
    with pytest.raises(TypeError):
        Status("x", State.HIDE, None, [], [], [], "", "extra")


def test_status_mutable_defaults_are_not_shared():
    a = Status("a")
    b = Status("b")
    a.info.append("x")
    a.detail.append("y")
    a.command.append({"z": 1})
    assert b.info == [] and b.detail == [] and b.command == []


def test_status_equality_and_mutability():
    a = Status("a", State.ACTIVE)
    assert a == Status("a", State.ACTIVE)
    assert a != Status("a", State.WARNING)
    a.state = State.WARNING
    assert a == Status("a", State.WARNING)


def test_status_is_unhashable():
    with pytest.raises(TypeError):
        hash(Status("a"))


def test_status_state_equal_to_plain_int():
    assert Status("a", State.ACTIVE) == Status("a", 3)


def test_status_asdict_and_replace():
    status = Status("a", State.MANUAL, [0.0, 0.0])
    assert dataclasses.asdict(status) == {
        "name": "a",
        "state": State.MANUAL,
        "location": [0.0, 0.0],
        "info": [],
        "detail": [],
        "command": [],
        "node": "",
    }
    replaced = dataclasses.replace(status, state=State.ERROR)
    assert replaced.state is State.ERROR
    assert status.state is State.MANUAL
