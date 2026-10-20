# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from types import SimpleNamespace

import pytest

from src.job import command
from src.job.active.domain import Variable
from src.job.task.common.control import controls_wait_logic, controls_wait_time
from blocks import block, boolean, num, seconds, text


class Sequence:
    """Fake value Logic returning the given values in order."""
    def __init__(self, *values):
        self.values = list(values)
        self.calls = 0

    async def exec(self):
        self.calls += 1
        return self.values.pop(0)


@pytest.fixture
def recorded_sleep(monkeypatch):
    calls = []

    async def fake_sleep(delay):
        calls.append(delay)

    fake_asyncio = SimpleNamespace(sleep=fake_sleep)
    monkeypatch.setattr(controls_wait_logic.logic, "asyncio", fake_asyncio)
    monkeypatch.setattr(controls_wait_time.logic, "asyncio", fake_asyncio)
    return calls


def log_block(message, level="INFO", name="log", **kwargs):
    return block("controls_log", name=name, message=text(message), level=level, **kwargs)


def messages(caplog):
    return [r.getMessage() for r in caplog.records if r.getMessage().startswith("log: ")]


# --- controls_log ---

@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR"])
async def test_controls_log_writes_at_level_and_shows_text(build_logic, caplog, level):
    logic = await build_logic(log_block("hello", level=level))
    with caplog.at_level(logging.DEBUG, logger="freedom.tests"):
        await logic.exec()
    assert [(r.levelname, r.getMessage()) for r in caplog.records] == [(level, "log: hello")]
    assert logic.domain.command == [command.Text("hello")]


async def test_controls_log_stringifies_non_text_values(build_logic, caplog):
    logic = await build_logic(block("controls_log", name="n", message=num(1.5)))
    with caplog.at_level(logging.INFO, logger="freedom.tests"):
        await logic.exec()
    assert caplog.records[-1].getMessage() == "n: 1.5"


async def test_controls_log_unknown_level_logs_nothing(build_logic, caplog):
    logic = await build_logic(log_block("x", level="TRACE"))
    with caplog.at_level(logging.DEBUG, logger="freedom.tests"):
        await logic.exec()
    assert caplog.records == []
    assert logic.domain.command == [command.Text("x")]


# --- controls_error ---

async def test_controls_error_raises_with_message(build_logic):
    logic = await build_logic(block("controls_error", error=text("boom")))
    with pytest.raises(RuntimeError, match="^boom$"):
        await logic.exec()
    assert logic.domain.command == [command.Text("boom")]


def test_controls_error_is_not_recoverable_by_default():
    from src.job.task import abstract
    domain = abstract.value.Domain.to_domain(block("controls_error", error=text("x")))
    assert domain.can_recover is False
    assert domain.name == "ジョブ異常"


# --- controls_error_msg / warning / warning_clear (need the active job node) ---

async def test_controls_error_msg_joins_job_errors(build_logic, active_job):
    logic = await build_logic(block("controls_error_msg"))
    assert await logic.exec() == ""
    active_job.domain.error_msg.add("E1")
    assert await logic.exec() == "E1"
    active_job.domain.error_msg.add("E2")
    assert sorted((await logic.exec()).split(", ")) == ["E1", "E2"]


async def test_controls_warning_adds_to_job_warnings(build_logic, active_job):
    logic = await build_logic(block("controls_warning", warning=text("low battery")))
    await logic.exec()
    await logic.exec()
    assert active_job.domain.warning_msg == {"low battery"}


async def test_controls_warning_clear_empties_job_warnings(build_logic, active_job):
    active_job.domain.warning_msg.update({"a", "b"})
    logic = await build_logic(block("controls_warning_clear"))
    await logic.exec()
    assert active_job.domain.warning_msg == set()


async def test_job_lookup_uses_job_id(build_logic, active_job):
    logic = await build_logic(block("controls_warning", warning=text("w")), job_id="other-job")
    with pytest.raises(IndexError):
        await logic.exec()


# --- controls_wait_time / controls_wait_logic ---

async def test_controls_wait_time_sleeps_for_interval(build_logic, recorded_sleep):
    logic = await build_logic(block("controls_wait_time", interval=seconds(2.5)))
    await logic.exec()
    assert recorded_sleep == [2.5]


async def test_controls_wait_logic_while_waits_until_condition_false(build_logic, recorded_sleep):
    logic = await build_logic(block("controls_wait_logic", mode="while", cond=boolean(True), interval=seconds(0.5)))
    logic._cond = Sequence(True, True, False)
    await logic.exec()
    assert logic._cond.calls == 3
    assert recorded_sleep == [0.5, 0.5]


async def test_controls_wait_logic_until_waits_until_condition_true(build_logic, recorded_sleep):
    logic = await build_logic(block("controls_wait_logic", mode="until", cond=boolean(False), interval=seconds(1)))
    logic._cond = Sequence(False, True)
    await logic.exec()
    assert recorded_sleep == [1.0]


async def test_controls_wait_logic_returns_immediately_when_already_satisfied(build_logic, recorded_sleep):
    logic = await build_logic(block("controls_wait_logic", mode="until", cond=boolean(True), interval=seconds(1)))
    await logic.exec()
    assert recorded_sleep == []


# --- controls_wait_manual ---

async def test_controls_wait_manual_waits_for_button(build_logic):
    logic = await build_logic(block("controls_wait_manual", label=text("OK")))
    task = asyncio.create_task(logic.exec())
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert logic.domain.command == [command.Button("OK", "OK")]
    assert not task.done()

    with pytest.raises(Exception, match="Failed to command"):
        await logic.exec_command("NG")
    assert not task.done()

    await logic.exec_command("OK")
    await asyncio.wait_for(task, timeout=1)
    assert logic.domain.command == []


async def test_controls_wait_manual_clears_button_on_cancel(build_logic):
    logic = await build_logic(block("controls_wait_manual", label=text("OK")))
    task = asyncio.create_task(logic.exec())
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert logic.domain.command == []


# --- controls_select ---

def select_block(var_id="sel"):
    choices = block("dict_create_with", KEY0=text("A"), VALUE0=num(1), KEY1=text("B"), VALUE1=num(2))
    return block("controls_select", var={"id": var_id}, map=choices)


async def test_controls_select_assigns_chosen_value(build_logic, active_job):
    var = Variable(id="sel", name="choice")
    active_job.domain.variables.append(var)
    logic = await build_logic(select_block())
    task = asyncio.create_task(logic.exec())
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert logic.domain.command == [command.Button("A", "A"), command.Button("B", "B")]

    with pytest.raises(Exception, match="Failed to command"):
        await logic.exec_command("C")

    await logic.exec_command("B")
    await asyncio.wait_for(task, timeout=1)
    assert var.value == 2
    assert logic.domain.command == [command.Text("B")]
    assert logic._map == {}


async def test_controls_select_requires_job_variable(build_logic, active_job):
    # next() on an empty generator inside a coroutine surfaces as RuntimeError (PEP 479)
    with pytest.raises(RuntimeError, match="StopIteration"):
        await build_logic(select_block("missing"))


# --- controls_try ---

async def test_controls_try_runs_init_try_finally(build_logic, caplog):
    content = block(
        "controls_try",
        init_task=log_block("init"),
        try_task=log_block("try", next=log_block("try2")),
        except_task=log_block("except"),
        finally_task=log_block("finally"),
    )
    logic = await build_logic(content)
    assert logic.domain.command == [command.Task(content["try_task"]["id"])]
    with caplog.at_level(logging.INFO, logger="freedom.tests"):
        await logic.exec()
    assert messages(caplog) == ["log: init", "log: try", "log: try2", "log: finally"]
    assert logic.domain.try_task.finished is True
    # init/except/finally run on deep copies, so they re-run after recovery
    assert logic.domain.init_task.finished is False
    assert logic.domain.finally_task.finished is False


async def test_controls_try_runs_except_and_reraises(build_logic, caplog):
    content = block(
        "controls_try",
        try_task=block("controls_error", error=text("boom"), next=log_block("unreached")),
        except_task=log_block("except"),
        finally_task=log_block("finally"),
    )
    logic = await build_logic(content)
    with caplog.at_level(logging.INFO, logger="freedom.tests"), pytest.raises(RuntimeError, match="boom"):
        await logic.exec()
    assert messages(caplog) == ["log: except", "log: finally"]


async def test_controls_try_retrieve_task_finds_nested_try_task(build_logic):
    inner = log_block("try")
    logic = await build_logic(block("controls_try", try_task=inner))
    found = logic.retrieve_task(inner["id"])
    assert found is logic._try_task


async def test_controls_try_with_no_children_is_a_noop(build_logic):
    logic = await build_logic(block("controls_try"))
    await logic.exec()
    assert logic.domain.command == []
