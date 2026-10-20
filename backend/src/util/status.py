# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import enum


class State(enum.IntEnum):
    """State
    Numeric values define the rendering layer order
    """
    HIDE = -1
    DISCONNECT = 0
    WAITING = 1
    MANUAL = 2
    ACTIVE = 3
    WARNING = 4
    ERROR = 5


@dataclasses.dataclass
class Status:
    """Node status
    Args:
        name (str): Name
        state (State): State
        location (list[float]): Location
        info (list[str]]): Information
        detail (list[str]]): Details
        command (list[dict]): Commands
        node (str): Node name
    """
    name:str
    state:State = State.HIDE
    location:list[float, float] = None
    info:list[str] = dataclasses.field(default_factory=list)
    detail:list[str] = dataclasses.field(default_factory=list)
    command:list[dict] = dataclasses.field(default_factory=list)
    node:str = ""
