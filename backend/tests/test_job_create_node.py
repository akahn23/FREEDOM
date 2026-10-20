import copy
import logging

import pytest

from src.job.create.node import Node


@pytest.fixture
def node():
    # Node.__init__ needs a registered log node and a DB interface; the parsing
    # helpers only use self, so bypass the constructor.
    return object.__new__(Node)


def number(id_, num):
    return {"type": "math_number", "id": id_, "fields": {"NUM": num}}


COMPARE_BLOCK = {
    "type": "logic_compare",
    "id": "cmp",
    "fields": {"OP": "LT"},
    "inputs": {
        "A": {"block": number("a", 1)},
        "B": {"shadow": number("b", 2)},
    },
}

# Shape produced by Blockly.serialization.workspaces.save()
WORKSPACE = {
    "blocks": {
        "languageVersion": 0,
        "blocks": [
            {
                "type": "controls_log",
                "id": "log1",
                "x": 10,
                "y": 20,
                "fields": {"LEVEL": "INFO"},
                "inputs": {"TEXT": {"shadow": {"type": "text", "id": "t1", "fields": {"TEXT": "hello"}}}},
                "next": {
                    "block": {
                        "type": "controls_wait_time",
                        "id": "wait1",
                        "inputs": {"TIME": {"block": number("n1", 5)}},
                    }
                },
            },
            {"type": "controls_log", "id": "orphan", "x": 300, "y": 300},
        ],
    },
    "variables": [{"name": "count", "id": "var1"}, {"name": "target", "id": "var2", "type": ""}],
}


def test_parse_minimal_block(node):
    assert node._parse_block({"type": "logic_null", "id": "x"}) == {"type": "logic_null", "id": "x"}


def test_parse_block_flattens_fields(node):
    assert node._parse_block(number("n", 3)) == {"type": "math_number", "id": "n", "NUM": 3}


def test_parse_block_ignores_layout_and_extra_keys(node):
    block = {"type": "text", "id": "t", "x": 1, "y": 2, "collapsed": True,
             "extraState": {"foo": 1}, "fields": {"TEXT": "a"}}
    assert node._parse_block(block) == {"type": "text", "id": "t", "TEXT": "a"}


def test_parse_block_inputs_from_block_and_shadow(node):
    assert node._parse_block(COMPARE_BLOCK) == {
        "type": "logic_compare",
        "id": "cmp",
        "OP": "LT",
        "A": {"type": "math_number", "id": "a", "NUM": 1},
        "B": {"type": "math_number", "id": "b", "NUM": 2},
    }


def test_parse_block_prefers_real_block_over_shadow(node):
    block = {"type": "logic_negate", "id": "neg", "inputs": {
        "BOOL": {"shadow": {"type": "logic_boolean", "id": "s", "fields": {"BOOL": "TRUE"}},
                 "block": {"type": "logic_boolean", "id": "b", "fields": {"BOOL": "FALSE"}}},
    }}
    assert node._parse_block(block)["BOOL"] == {"type": "logic_boolean", "id": "b", "BOOL": "FALSE"}


def test_parse_block_falls_back_to_shadow_when_block_is_none(node):
    block = {"type": "logic_negate", "id": "neg", "inputs": {
        "BOOL": {"block": None, "shadow": {"type": "logic_boolean", "id": "s"}}}}
    assert node._parse_block(block)["BOOL"] == {"type": "logic_boolean", "id": "s"}


def test_parse_block_nested_inputs_recursively(node):
    block = {"type": "logic_negate", "id": "neg", "inputs": {"BOOL": {"block": COMPARE_BLOCK}}}
    parsed = node._parse_block(block)
    assert parsed["BOOL"]["A"] == {"type": "math_number", "id": "a", "NUM": 1}


def test_parse_block_follows_next_chain(node):
    block = {"type": "s1", "id": "1", "next": {"block": {
        "type": "s2", "id": "2", "next": {"block": {"type": "s3", "id": "3"}}}}}
    assert node._parse_block(block) == {
        "type": "s1", "id": "1",
        "next": {"type": "s2", "id": "2", "next": {"type": "s3", "id": "3"}},
    }


def test_parse_block_statement_input_with_next(node):
    block = {"type": "controls_try", "id": "try", "inputs": {"DO": {"block": {
        "type": "s1", "id": "1", "next": {"block": {"type": "s2", "id": "2"}}}}}}
    assert node._parse_block(block)["DO"] == {"type": "s1", "id": "1", "next": {"type": "s2", "id": "2"}}


def test_parse_block_inputs_override_same_named_fields(node):
    block = {"type": "x", "id": "1", "fields": {"A": "field"}, "inputs": {"A": {"block": {"type": "y", "id": "2"}}}}
    assert node._parse_block(block)["A"] == {"type": "y", "id": "2"}


def test_parse_block_does_not_mutate_input(node):
    block = copy.deepcopy(COMPARE_BLOCK)
    node._parse_block(block)
    assert block == COMPARE_BLOCK


@pytest.mark.parametrize("block", [{"id": "x"}, {"type": "x"}])
def test_parse_block_requires_type_and_id(node, block):
    with pytest.raises(KeyError):
        node._parse_block(block)


def test_parse_block_input_without_block_or_shadow_raises(node):
    # Blockly's serializer omits unconnected inputs, so this only happens with hand-made JSON.
    with pytest.raises(KeyError):
        node._parse_block({"type": "x", "id": "1", "inputs": {"A": {}}})


def test_to_task_processes_only_first_top_level_block(node):
    task, variables = node._to_task(WORKSPACE)
    assert task == {
        "type": "controls_log",
        "id": "log1",
        "LEVEL": "INFO",
        "TEXT": {"type": "text", "id": "t1", "TEXT": "hello"},
        "next": {
            "type": "controls_wait_time",
            "id": "wait1",
            "TIME": {"type": "math_number", "id": "n1", "NUM": 5},
        },
    }
    assert variables == WORKSPACE["variables"]


def test_to_task_returns_variables_list_by_reference(node):
    workspace = copy.deepcopy(WORKSPACE)
    _, variables = node._to_task(workspace)
    assert variables is workspace["variables"]


@pytest.mark.parametrize("workspace", [
    {},
    {"blocks": {}},
    {"blocks": {"languageVersion": 0, "blocks": []}},
], ids=["empty", "no-blocks-list", "empty-blocks-list"])
def test_to_task_empty_workspace(node, workspace):
    assert node._to_task(workspace) == ({}, [])


def test_to_task_variables_without_blocks(node):
    variables = [{"name": "v", "id": "1"}]
    assert node._to_task({"variables": variables}) == ({}, variables)


def test_parsed_task_converts_to_task_domain(node):
    from src.job.task.abstract.value import Domain
    from src.job.task.common.logic import logic_compare
    from src.job.task.common.math import math_number

    task, _ = node._to_task({"blocks": {"blocks": [COMPARE_BLOCK]}})
    domain = Domain.to_domain(task)
    assert isinstance(domain, logic_compare.Domain)
    assert domain.OP == "LT"
    assert isinstance(domain.A, math_number.Domain) and domain.A.NUM == 1
    assert isinstance(domain.B, math_number.Domain) and domain.B.NUM == 2


class FakeAccess:
    def __init__(self, workspace=None):
        self.workspace = workspace
        self.calls = []

    async def fetch_name_list(self, user_id=None, is_admin=False):
        self.calls.append(("fetch_name_list", user_id, is_admin))
        return ["job1"]

    async def fetch_workspace(self, name):
        self.calls.append(("fetch_workspace", name))
        return copy.deepcopy(self.workspace)

    async def update(self, name, workspace):
        self.calls.append(("update", name, workspace))

    async def delete(self, name):
        self.calls.append(("delete", name))


@pytest.fixture
def wired_node(node):
    node._access = FakeAccess(WORKSPACE)
    node._logger = logging.getLogger("test.job.create")
    return node


async def test_access_methods_delegate_to_interface(wired_node):
    assert await wired_node.fetch_name_list(user_id="u", is_admin=True) == ["job1"]
    assert await wired_node.fetch_workspace("job1") == WORKSPACE
    await wired_node.update("job1", {"blocks": {}})
    await wired_node.delete("job1")
    assert wired_node._access.calls == [
        ("fetch_name_list", "u", True),
        ("fetch_workspace", "job1"),
        ("update", "job1", {"blocks": {}}),
        ("delete", "job1"),
    ]


async def test_active_inserts_parsed_task_with_variable_values(wired_node, monkeypatch):
    from src import job
    from src.repository import repository

    inserted = []

    class FakeActiveRepository(job.active.Repository):
        async def insert(self, name, task, variables):
            inserted.append((name, task, variables))
            return "job-id"

    active_repo = object.__new__(FakeActiveRepository)
    active_repo.data = []
    monkeypatch.setattr(repository, "data", [active_repo])

    assert await wired_node.active("job1", count=3) == "job-id"
    name, task, variables = inserted[0]
    assert name == "job1"
    assert task == wired_node._to_task(WORKSPACE)[0]
    assert variables == [
        {"name": "count", "id": "var1", "value": 3},
        {"name": "target", "id": "var2", "type": "", "value": None},
    ]
