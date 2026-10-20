# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta

import pytest

from src.job.active.domain import Variable
from src.job.task.common.time import _time_now
from blocks import block, num, seconds

T0 = datetime(2026, 4, 1, 9, 0, 0)


class Value:
    """Fake value Logic."""
    def __init__(self, value):
        self.value = value

    async def exec(self):
        return self.value


@pytest.fixture
def time_vars(active_job):
    t = Variable(id="t", name="start", type="Time", value=T0)
    d = Variable(id="d", name="delta", type="TimeDelta", value=timedelta(minutes=5))
    active_job.domain.variables.extend([t, d])
    return t, d


# --- _time_now ---

async def test_time_now_returns_current_time(build_logic, monkeypatch):
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return T0

    monkeypatch.setattr(_time_now.logic, "datetime", FrozenDatetime)
    logic = await build_logic(block("_time_now"))
    assert await logic.exec() == T0


async def test_time_now_is_live(build_logic):
    logic = await build_logic(block("_time_now"))
    before = datetime.now()
    value = await logic.exec()
    assert before <= value <= datetime.now()


# --- time_delta_duration ---

@pytest.mark.parametrize("unit, amount, expected", [
    ("seconds", 30, timedelta(seconds=30)),
    ("minutes", 1.5, timedelta(seconds=90)),
    ("hours", 2, timedelta(hours=2)),
])
async def test_time_delta_duration_units(build_logic, unit, amount, expected):
    logic = await build_logic(block("time_delta_duration", time=num(amount), unit=unit))
    assert await logic.exec() == expected


async def test_time_delta_duration_rejects_unknown_unit(build_logic):
    logic = await build_logic(block("time_delta_duration", time=num(1), unit="fortnights"))
    with pytest.raises(TypeError):
        await logic.exec()


# --- time_delta_arithmetic ---

async def arithmetic(build_logic, left, operator, right):
    logic = await build_logic(block("time_delta_arithmetic", LEFT=num(0), RIGHT=num(0), operator=operator))
    logic._LEFT, logic._RIGHT = Value(left), Value(right)
    return logic


@pytest.mark.parametrize("left, operator, right, expected", [
    (T0, "+", timedelta(hours=1), datetime(2026, 4, 1, 10, 0, 0)),
    (T0, "-", timedelta(minutes=30), datetime(2026, 4, 1, 8, 30, 0)),
    (datetime(2026, 4, 1, 9, 5), "-", T0, timedelta(minutes=5)),
    (timedelta(seconds=10), "×", 3, timedelta(seconds=30)),
    (timedelta(minutes=1), "÷", 4, timedelta(seconds=15)),
    (timedelta(minutes=1), "÷", timedelta(seconds=15), 4.0),
])
async def test_time_delta_arithmetic_operators(build_logic, left, operator, right, expected):
    logic = await arithmetic(build_logic, left, operator, right)
    assert await logic.exec() == expected


async def test_time_delta_arithmetic_default_operator_is_subtract(build_logic):
    logic = await build_logic(block("time_delta_arithmetic", LEFT=seconds(10), RIGHT=seconds(4)))
    assert logic.domain.operator == "-"
    assert await logic.exec() == timedelta(seconds=6)


@pytest.mark.parametrize("left, operator, right", [
    (T0, "+", T0),
    (T0, "×", 2),
    (timedelta(seconds=1), "÷", 0),
])
async def test_time_delta_arithmetic_invalid_operation_raises_job_error(build_logic, caplog, left, operator, right):
    logic = await arithmetic(build_logic, left, operator, right)
    with pytest.raises(Exception, match="時間計算の演算に失敗"):
        await logic.exec()
    assert "Failed to time_delta_arithmetic" in caplog.text


async def test_time_delta_arithmetic_unknown_operator_returns_none(build_logic):
    logic = await arithmetic(build_logic, T0, "%", T0)
    assert await logic.exec() is None


# --- time variables ---

async def test_time_get_returns_variable(build_logic, time_vars):
    logic = await build_logic(block("_time__get", VAR={"id": "t"}))
    assert await logic.exec() == T0


async def test_time_set_assigns_variable(build_logic, time_vars):
    logic = await build_logic(block("_time__set", VAR={"id": "t"}, VALUE=block("time_delta_arithmetic", LEFT=block("_time__get", VAR={"id": "t"}), RIGHT=seconds(60), operator="+")))
    await logic.exec()
    assert time_vars[0].value == datetime(2026, 4, 1, 9, 1, 0)


async def test_time_delta_get_returns_variable(build_logic, time_vars):
    logic = await build_logic(block("time_delta__get", VAR={"id": "d"}))
    assert await logic.exec() == timedelta(minutes=5)


async def test_time_delta_set_assigns_variable(build_logic, time_vars):
    logic = await build_logic(block("time_delta__set", VAR={"id": "d"}, VALUE=seconds(12)))
    await logic.exec()
    assert time_vars[1].value == timedelta(seconds=12)


async def test_time_variable_missing_raises(build_logic, time_vars):
    # next() on an empty generator inside a coroutine surfaces as RuntimeError (PEP 479)
    with pytest.raises(RuntimeError, match="StopIteration"):
        await build_logic(block("_time__get", VAR={"id": "nope"}))
