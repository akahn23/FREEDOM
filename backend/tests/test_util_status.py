# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import enum

from src.util.status import State, Status


def test_state_is_int_enum():
    assert issubclass(State, enum.IntEnum)


def test_state_values():
    assert {s.name: s.value for s in State} == {
        "HIDE": -1,
        "DISCONNECT": 0,
        "WAITING": 1,
        "MANUAL": 2,
        "ACTIVE": 3,
        "WARNING": 4,
        "ERROR": 5,
    }
    assert State.HIDE == -1


def test_state_ordering():
    assert State.ERROR > State.WARNING > State.ACTIVE > State.MANUAL > State.WAITING > State.DISCONNECT > State.HIDE
    assert State.ERROR > State.ACTIVE
    assert max(State) is State.ERROR
    assert min(State) is State.HIDE
    assert sorted([State.ERROR, State.HIDE, State.ACTIVE]) == [State.HIDE, State.ACTIVE, State.ERROR]


def test_state_from_int():
    assert State(3) is State.ACTIVE


def test_status_defaults():
    status = Status(name="robot_1")
    assert status.name == "robot_1"
    assert status.state == State.HIDE
    assert status.location is None
    assert status.info == []
    assert status.detail == []
    assert status.command == []
    assert status.node == ""


def test_status_default_lists_are_independent():
    first = Status(name="first")
    second = Status(name="second")
    for field in ("info", "detail", "command"):
        assert getattr(first, field) is not getattr(second, field)
    assert first.info is not first.detail
    first.info.append("battery low")
    first.detail.append("detail")
    first.command.append({"func": "stop"})
    assert second.info == []
    assert second.detail == []
    assert second.command == []


def test_status_explicit_values():
    status = Status(
        name="lamp_1",
        state=State.ERROR,
        location=[35.0, 137.0],
        info=["info"],
        detail=["detail"],
        command=[{"func": "reset"}],
        node="infrastructure.lamp",
    )
    assert status.state is State.ERROR
    assert status.location == [35.0, 137.0]
    assert status.info == ["info"]
    assert status.detail == ["detail"]
    assert status.command == [{"func": "reset"}]
    assert status.node == "infrastructure.lamp"
