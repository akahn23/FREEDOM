# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

"""Helpers that build Blockly-style task dicts for tests."""

import itertools

_ids = itertools.count()


def block(type_: str, **fields) -> dict:
    return {"type": type_, "id": f"{type_}-{next(_ids)}", **fields}


def num(value) -> dict:
    return block("math_number", NUM=value)


def text(value: str) -> dict:
    return block("text", TEXT=value)


def boolean(value: bool) -> dict:
    return block("logic_boolean", BOOL="TRUE" if value else "FALSE")


def seconds(value) -> dict:
    return block("time_delta_duration", time=num(value), unit="seconds")
