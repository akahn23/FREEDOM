# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

import pytest

from src.job.active.domain import Variable
from src.job.task import abstract, common
from blocks import block, num, text


def get_var(var_id="d"):
    return block("_dict_get", VAR={"id": var_id})


@pytest.fixture
def dict_var(active_job):
    var = Variable(id="d", name="my_dict", type="Dict", value={"a": 1})
    active_job.domain.variables.append(var)
    return var


# --- dict_create_with ---

def test_dict_create_with_builds_dynamic_fields():
    domain = abstract.value.Domain.to_domain(block("dict_create_with", KEY0=text("a"), VALUE0=num(1), KEY1=text("b")))
    names = {f.name for f in dataclasses.fields(domain)}
    assert {"KEY0", "VALUE0", "KEY1"} <= names
    assert isinstance(domain.KEY0, common.text.text.Domain)
    assert isinstance(domain.VALUE0, common.math.math_number.Domain)


async def test_dict_create_with_pairs_keys_and_values(build_logic):
    logic = await build_logic(block("dict_create_with", KEY0=text("a"), VALUE0=num(1), KEY1=text("b"), VALUE1=text("x")))
    assert await logic.exec() == {"a": 1, "b": "x"}


async def test_dict_create_with_missing_value_is_none(build_logic):
    logic = await build_logic(block("dict_create_with", KEY0=text("a")))
    assert await logic.exec() == {"a": None}


async def test_dict_create_with_orders_keys_numerically(build_logic):
    fields = {f"KEY{i}": text(f"k{i}") for i in (10, 2, 0)}
    logic = await build_logic(block("dict_create_with", **fields))
    assert list(await logic.exec()) == ["k0", "k2", "k10"]


async def test_dict_create_with_empty(build_logic):
    logic = await build_logic(block("dict_create_with"))
    assert await logic.exec() == {}


async def test_dict_create_with_returns_new_dict_each_exec(build_logic):
    logic = await build_logic(block("dict_create_with", KEY0=text("a"), VALUE0=num(1)))
    first = await logic.exec()
    first["a"] = 99
    assert await logic.exec() == {"a": 1}


# --- _dict_get / _dict_set ---

async def test_dict_get_returns_job_variable(build_logic, dict_var):
    logic = await build_logic(get_var())
    assert await logic.exec() is dict_var.value


async def test_dict_get_unknown_variable_raises(build_logic, dict_var):
    # next() on an empty generator inside a coroutine surfaces as RuntimeError (PEP 479)
    with pytest.raises(RuntimeError, match="StopIteration"):
        await build_logic(get_var("missing"))


async def test_dict_set_assigns_job_variable(build_logic, dict_var):
    logic = await build_logic(block("_dict_set", VAR={"id": "d"}, VALUE=block("dict_create_with", KEY0=text("z"), VALUE0=num(0))))
    await logic.exec()
    assert dict_var.value == {"z": 0}


# --- dict_get_item ---

async def test_dict_get_item_get(build_logic, dict_var):
    logic = await build_logic(block("dict_get_item", DICT=get_var(), MODE="GET", KEY=text("a")))
    assert await logic.exec() == 1
    assert dict_var.value == {"a": 1}


async def test_dict_get_item_missing_key_returns_none(build_logic, dict_var):
    logic = await build_logic(block("dict_get_item", DICT=get_var(), KEY=text("nope")))
    assert await logic.exec() is None


async def test_dict_get_item_get_remove(build_logic, dict_var):
    logic = await build_logic(block("dict_get_item", DICT=get_var(), MODE="GET_REMOVE", KEY=text("a")))
    assert await logic.exec() == 1
    assert dict_var.value == {}
    assert await logic.exec() is None


async def test_dict_get_item_unknown_mode_returns_none(build_logic, dict_var):
    logic = await build_logic(block("dict_get_item", DICT=get_var(), MODE="POP", KEY=text("a")))
    assert await logic.exec() is None


# --- dict_set_item ---

async def test_dict_set_item_mutates_variable_in_place(build_logic, dict_var):
    logic = await build_logic(block("dict_set_item", DICT=get_var(), KEY=text("b"), VALUE=num(2)))
    original = dict_var.value
    await logic.exec()
    assert dict_var.value is original
    assert dict_var.value == {"a": 1, "b": 2}


async def test_dict_set_item_overwrites_existing_key(build_logic, dict_var):
    logic = await build_logic(block("dict_set_item", DICT=get_var(), KEY=text("a"), VALUE=text("new")))
    await logic.exec()
    assert dict_var.value == {"a": "new"}


async def test_dict_set_item_empty_key_and_value_sockets_use_none(build_logic, dict_var):
    logic = await build_logic(block("dict_set_item", DICT=get_var(), KEY=None, VALUE=None))
    await logic.exec()
    assert dict_var.value == {"a": 1, None: None}
