import logging

import pytest

from src.job.task.abstract.value import Domain as ValueDomain
from src.job.task.common.logic.logic_compare import Domain, Logic

LOGGER = logging.getLogger("test.logic_compare")


class Stub:
    def __init__(self, value):
        self.value = value
        self.calls = 0

    async def exec(self):
        self.calls += 1
        return self.value


def compare(op, a, b):
    """Logic with stubbed operand logics so arbitrary Python values can be compared."""
    logic = Logic(Domain(type="logic_compare", id="cmp", OP=op), 1, LOGGER)
    logic._A = Stub(a)
    logic._B = Stub(b)
    return logic


def operand(value):
    if value is None:
        return {"type": "logic_null", "id": "null"}
    if isinstance(value, bool):
        return {"type": "logic_boolean", "id": "bool", "BOOL": "TRUE" if value else "FALSE"}
    if isinstance(value, str):
        return {"type": "text", "id": "text", "TEXT": value}
    return {"type": "math_number", "id": "num", "NUM": value}


async def compare_blocks(op, a, b):
    """Build the domain the same way active jobs do (dict -> Domain -> make_logic)."""
    domain = ValueDomain.to_domain({"type": "logic_compare", "id": "cmp", "OP": op,
                                    "A": operand(a), "B": operand(b)})
    logic = await domain.make_logic(1, LOGGER)
    return await logic.exec()


TRUTH_TABLE = [
    # op,   1 vs 2, 2 vs 2, 3 vs 2
    ("EQ",  False, True,  False),
    ("NEQ", True,  False, True),
    ("LT",  True,  False, False),
    ("LTE", True,  True,  False),
    ("GT",  False, False, True),
    ("GTE", False, True,  True),
]
CASES = [(op, a, 2, expected)
         for op, *results in TRUTH_TABLE
         for a, expected in zip((1, 2, 3), results)]


@pytest.mark.parametrize("op, a, b, expected", CASES)
async def test_numeric_operators(op, a, b, expected):
    assert await compare(op, a, b).exec() is expected


@pytest.mark.parametrize("op, a, b, expected", CASES)
async def test_operators_via_math_number_blocks(op, a, b, expected):
    assert await compare_blocks(op, a, b) is expected


@pytest.mark.parametrize("op, a, b, expected", [
    ("EQ", 2, 2.0, True),
    ("LT", 1.5, 2, True),
    ("GTE", -0.0, 0.0, True),
])
async def test_int_float_mix(op, a, b, expected):
    assert await compare(op, a, b).exec() is expected


@pytest.mark.parametrize("op, a, b, expected", [
    ("EQ", "abc", "abc", True),
    ("NEQ", "abc", "abd", True),
    ("LT", "abc", "abd", True),
    ("LT", "B", "a", True),   # ordinal (case-sensitive) comparison
    ("GTE", "b", "a", True),
    ("LTE", "", "a", True),
])
async def test_text_operands(op, a, b, expected):
    assert await compare_blocks(op, a, b) is expected


@pytest.mark.parametrize("op, a, b, expected", [
    ("EQ", True, True, True),
    ("NEQ", True, False, True),
    ("GT", True, False, True),
])
async def test_boolean_operands(op, a, b, expected):
    assert await compare_blocks(op, a, b) is expected


@pytest.mark.parametrize("op, expected", [("EQ", False), ("NEQ", True)])
async def test_equality_across_types_does_not_raise(op, expected):
    assert await compare(op, "1", 1).exec() is expected
    assert await compare_blocks(op, "1", 1) is expected


@pytest.mark.parametrize("op", ["LT", "LTE", "GT", "GTE"])
@pytest.mark.parametrize("a, b", [("1", 1), (1, "1"), ([1], 1), ({}, {})])
async def test_ordering_across_incompatible_types_raises_type_error(op, a, b):
    with pytest.raises(TypeError):
        await compare(op, a, b).exec()


async def test_bool_and_number_compare_with_python_semantics():
    assert await compare("EQ", True, 1).exec() is True
    assert await compare("LT", False, 1).exec() is True


@pytest.mark.parametrize("op, expected", [("EQ", True), ("NEQ", False)])
async def test_missing_operands_are_none(op, expected):
    logic = Logic(Domain(type="logic_compare", id="cmp", OP=op), 1, LOGGER)
    await logic.init()
    assert logic._A is None and logic._B is None
    assert await logic.exec() is expected


async def test_one_missing_operand():
    domain = ValueDomain.to_domain({"type": "logic_compare", "id": "cmp", "OP": "EQ", "A": operand(1)})
    logic = await domain.make_logic(1, LOGGER)
    assert logic._B is None
    assert await logic.exec() is False


@pytest.mark.parametrize("op, expected", [("EQ", True), ("NEQ", False)])
async def test_logic_null_operands(op, expected):
    assert await compare_blocks(op, None, None) is expected


@pytest.mark.parametrize("op", ["LT", "LTE", "GT", "GTE"])
@pytest.mark.parametrize("a, b", [(None, None), (None, 1), (1, None)])
async def test_ordering_with_none_raises_type_error(op, a, b):
    with pytest.raises(TypeError):
        await compare(op, a, b).exec()


@pytest.mark.parametrize("op", ["", "eq", "==", "LE", None])
async def test_unknown_operator_raises_value_error(op):
    with pytest.raises(ValueError, match="Unknown operator"):
        await compare(op, 1, 1).exec()


async def test_default_domain_operator_is_rejected():
    logic = Logic(Domain(type="logic_compare", id="cmp"), 1, LOGGER)
    await logic.init()
    with pytest.raises(ValueError):
        await logic.exec()


async def test_operands_are_evaluated_on_every_exec():
    logic = compare("EQ", 1, 1)
    await logic.exec()
    await logic.exec()
    assert logic._A.calls == 2 and logic._B.calls == 2


async def test_operands_evaluated_even_when_operator_unknown():
    logic = compare("??", 1, 1)
    with pytest.raises(ValueError):
        await logic.exec()
    assert logic._A.calls == 1 and logic._B.calls == 1


def test_domain_toolbox_and_block_definitions():
    assert Domain.define_block() == []
    assert Domain.define_toolbox() == [{"kind": "block", "type": "logic_compare"}]


def test_domain_converts_operand_dicts_to_domains():
    from src.job.task.common.math import math_number
    domain = Domain(type="logic_compare", id="cmp", OP="EQ", A=operand(1), B=operand(2))
    assert isinstance(domain.A, math_number.Domain)
    assert isinstance(domain.B, math_number.Domain)
