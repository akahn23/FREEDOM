# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.util.status import State, Status


def test_state_codes():
    assert {s.name: s.value for s in State} == {
        "HIDE": -1, "DISCONNECT": 0, "WAITING": 1, "MANUAL": 2, "ACTIVE": 3, "WARNING": 4, "ERROR": 5,
    }


def test_state_is_ordered_by_draw_layer():
    assert sorted([State.ERROR, State.HIDE, State.ACTIVE, State.WAITING]) == [
        State.HIDE, State.WAITING, State.ACTIVE, State.ERROR,
    ]
    assert max(State) is State.ERROR
    assert State.WARNING > State.ACTIVE


def test_state_compares_with_int():
    assert State(3) is State.ACTIVE
    assert State.ERROR == 5


def test_status_defaults():
    status = Status("lamp_1")
    assert status.state is State.HIDE
    assert status.location is None
    assert (status.info, status.detail, status.command, status.node) == ([], [], [], "")


def test_status_list_defaults_are_not_shared():
    a, b = Status("a"), Status("b")
    a.info.append("x")
    a.command.append({"type": "button"})
    assert b.info == [] and b.command == []


def test_status_asdict():
    status = Status("amr", State.WARNING, [1.0, 2.0], ["i"], ["d"], [{"c": 1}], "robot.dummy")
    assert dataclasses.asdict(status) == {
        "name": "amr", "state": State.WARNING, "location": [1.0, 2.0],
        "info": ["i"], "detail": ["d"], "command": [{"c": 1}], "node": "robot.dummy",
    }
