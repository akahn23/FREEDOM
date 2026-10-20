# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import pytest

from src.job import command
from src.job.task import abstract, common
from blocks import block, num, text


def log(message: str, **kwargs) -> dict:
    return block("controls_log", message=text(message), **kwargs)


def test_to_domain_resolves_common_block_by_type():
    domain = abstract.value.Domain.to_domain(num(3))
    assert isinstance(domain, common.math.math_number.Domain)
    assert domain.NUM == 3


def test_to_domain_converts_nested_value_fields():
    domain = abstract.value.Domain.to_domain(block("time_delta_duration", time=num(2), unit="minutes"))
    assert isinstance(domain, common.time.time_delta_duration.Domain)
    assert isinstance(domain.time, common.math.math_number.Domain)


def test_to_domain_converts_next_chain_and_statement_defaults():
    domain = abstract.value.Domain.to_domain(log("first", next=log("second")))
    assert isinstance(domain, common.control.controls_log.Domain)
    assert isinstance(domain.next, common.control.controls_log.Domain)
    assert domain.next.next is None
    assert (domain.should_show, domain.can_recover, domain.finished, domain.command) == (True, True, False, [])


def test_statement_command_dicts_become_command_objects():
    domain = abstract.value.Domain.to_domain(log("x", command=[{"type": "text", "label": "hi"}, {"type": "task", "id": "t1"}]))
    assert domain.command == [command.Text("hi"), command.Task("t1")]


def test_to_domain_unknown_type_raises():
    with pytest.raises(ModuleNotFoundError):
        abstract.value.Domain.to_domain(block("no_such_block"))


def test_abstract_value_domain_cannot_be_instantiated():
    with pytest.raises(TypeError):
        abstract.value.Domain(type="x", id="y")


async def test_make_logic_returns_matching_logic_and_runs_init(build_logic):
    logic = await build_logic(log("a", next=log("b")))
    assert isinstance(logic, common.control.controls_log.Logic)
    assert isinstance(logic.next, common.control.controls_log.Logic)
    assert logic.next.next is None


async def test_retrieve_task_by_id_and_running_task(build_logic):
    first, second = log("a"), log("b")
    first["next"] = second
    logic = await build_logic(first)
    assert logic.retrieve_task(first["id"]) is logic
    assert logic.retrieve_task(second["id"]) is logic.next
    assert logic.retrieve_task("missing") is None
    assert logic.retrieve_task() is logic
    logic.domain.finished = True
    assert logic.retrieve_task() is logic.next
    logic.next.domain.finished = True
    assert logic.retrieve_task() is None


async def test_default_exec_command_raises(build_logic):
    logic = await build_logic(log("a"))
    with pytest.raises(Exception, match="Failed to command"):
        await logic.exec_command("anything")
