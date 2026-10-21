import asyncio
import importlib
import inspect
import logging
import math
import pkgutil
import types
from unittest.mock import AsyncMock

import pytest
from src import equipment, freedom, infrastructure, job, robot  # noqa: F401
from src.job import command
from src.job.active import Variable
from src.job.task import abstract
from src.job.task.common.loop.exception import LoopBreak, LoopContinue
from src.job.task.job.active import exception as job_exception
from src.repository import repository

LOGGER = logging.getLogger("tests.job.task")
JOB_ID = "job-under-test"


# ---------------------------------------------------------------- helpers

def num(value, id="num"):
    return {"type": "math_number", "id": id, "NUM": value}


def txt(value, id="txt"):
    return {"type": "text", "id": id, "TEXT": value}


def boolean(value, id="bool"):
    return {"type": "logic_boolean", "id": id, "BOOL": "TRUE" if value else "FALSE"}


def lst(*items, id="list"):
    return {"type": "lists_create_with", "id": id, **{f"ADD{i}": item for i, item in enumerate(items)}}


def compare(a, op, b, id="cmp"):
    return {"type": "logic_compare", "id": id, "OP": op, "A": a, "B": b}


def arith(a, op, b, id="arith"):
    return {"type": "math_arithmetic", "id": id, "OP": op, "A": a, "B": b}


def get_var(var_id, kind="math"):
    return {"type": f"_{kind}_get", "id": f"get-{var_id}", "VAR": {"id": var_id}}


def set_var(var_id, value, id=None, next=None):
    block = {"type": "_math_set", "id": id or f"set-{var_id}", "VAR": {"id": var_id}, "VALUE": value}
    if next is not None:
        block["next"] = next
    return block


def increment(var_id, id=None, next=None):
    return set_var(var_id, arith(get_var(var_id), "ADD", num(1)), id=id, next=next)


def build(block):
    return abstract.value.Domain.to_domain(block)


def evaluate(block):
    async def run():
        logic = await build(block).make_logic(JOB_ID, LOGGER)
        return await logic.exec()
    return asyncio.run(run())


def run_statements(block):
    async def run():
        logic = await build(block).make_logic(JOB_ID, LOGGER)
        await command.Task(logic.domain.id).exec(logic, LOGGER)
        return logic
    return asyncio.run(run())


@pytest.fixture
def job_node():
    node = object.__new__(job.active.Node)
    node.domain = types.SimpleNamespace(
        id=JOB_ID, name="job", variables=[], warning_msg=set(), error_msg=set(),
    )
    repository.append(node)
    yield node
    repository.remove(node)


def add_var(node, var_id, value=None, type=None):
    var = Variable(id=var_id, name=var_id, type=type, value=value)
    node.domain.variables.append(var)
    return var


# ---------------------------------------------------- domain construction

def test_to_domain_resolves_common_block_by_name():
    domain = build(num(5))
    assert type(domain).__module__ == "src.job.task.common.math.math_number.domain"
    assert domain.NUM == 5
    assert domain.id == "num"


def test_to_domain_resolves_dotted_type_to_package():
    domain = build({"type": "robot.dummy.place", "id": "p",
                    "robot": num(0), "location": num(0)})
    assert type(domain).__module__ == "src.job.task.robot.dummy.place.domain"
    assert domain.name == "\u30c0\u30df\u30fc\u914d\u7f6e"


def test_nested_value_dicts_become_domains():
    domain = build(arith(num(1, id="a"), "ADD", num(2, id="b")))
    assert isinstance(domain.A, abstract.value.Domain)
    assert (domain.A.id, domain.B.NUM) == ("a", 2)


def test_missing_nested_value_raises_type_error():
    with pytest.raises(TypeError):
        build({"type": "math_arithmetic", "id": "x", "OP": "ADD", "A": num(1)})


def test_unknown_block_type_raises():
    with pytest.raises(ModuleNotFoundError):
        build({"type": "no_such_block", "id": "x"})


def test_statement_domain_converts_command_dicts():
    domain = build({
        "type": "controls_warning_clear", "id": "w",
        "command": [
            {"type": "button", "label": "OK", "value": 1},
            {"type": "switch", "label_on": "on", "label_off": "off", "value": True},
            {"type": "text", "label": "hi"},
            {"type": "task", "id": "child"},
        ],
    })
    assert domain.command == [
        command.Button("OK", 1),
        command.Switch("on", "off", True),
        command.Text("hi"),
        command.Task("child"),
    ]


def test_statement_next_chain_is_converted():
    domain = build({"type": "controls_warning_clear", "id": "a",
                    "next": {"type": "controls_warning_clear", "id": "b"}})
    assert isinstance(domain.next, abstract.statement.Domain)
    assert domain.next.id == "b" and domain.next.next is None


def _block_packages():
    root = importlib.import_module("src.job.task")
    for info in pkgutil.walk_packages(root.__path__, root.__name__ + "."):
        if not info.ispkg or ".abstract" in info.name:
            continue
        module = importlib.import_module(info.name)
        domain = getattr(module, "Domain", None)
        if isinstance(domain, type) and domain.__module__ == info.name + ".domain":
            yield info.name


BLOCK_PACKAGES = sorted(_block_packages())


def test_map_and_job_exec_blocks_use_registered_nodes(block_context):
    location_cls = importlib.import_module("src.job.task.common.map.location_create").Domain
    assert location_cls.define_block()[0]["args0"][0]["value"] == [35.0, 137.0]
    exec_cls = importlib.import_module("src.job.task.job.active.exec").Domain
    blocks = asyncio.run(exec_cls.define_block())
    assert ["job_a", "job_a"] in str_lists(blocks)


def str_lists(obj):
    if isinstance(obj, list):
        if all(isinstance(x, str) for x in obj) and obj:
            yield obj
        for x in obj:
            yield from str_lists(x)
    elif isinstance(obj, dict):
        for x in obj.values():
            yield from str_lists(x)


def test_block_packages_discovered():
    assert len(BLOCK_PACKAGES) > 90


@pytest.fixture
def block_context():
    map_node = object.__new__(freedom.map.Node)
    map_node.domain = types.SimpleNamespace(default_view=types.SimpleNamespace(center=[35.0, 137.0]))
    create_node = object.__new__(job.create.Node)
    create_node.fetch_name_list = AsyncMock(return_value=["job_a", "job_b"])
    repository.extend([map_node, create_node])
    yield
    repository.remove(map_node)
    repository.remove(create_node)


async def _resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.mark.parametrize("package", BLOCK_PACKAGES)
def test_every_block_defines_block_and_toolbox(package, block_context):
    domain_cls = importlib.import_module(package).Domain
    blocks = asyncio.run(_resolve(domain_cls.define_block()))
    toolbox = asyncio.run(_resolve(domain_cls.define_toolbox()))
    assert isinstance(blocks, list)
    assert isinstance(toolbox, list)
    short = package.removeprefix("src.job.task.")
    expected = {short, short.rsplit(".", 1)[-1]}
    assert all(block["type"] in expected for block in blocks)
    assert all(isinstance(entry, dict) for entry in toolbox)


# ----------------------------------------------------------------- math

@pytest.mark.parametrize(("op", "expected"), [
    ("ADD", 9), ("MINUS", 5), ("MULTIPLY", 14), ("DIVIDE", 3.5), ("POWER", 49),
])
def test_math_arithmetic(op, expected):
    assert evaluate(arith(num(7), op, num(2))) == expected


def test_math_arithmetic_unknown_op():
    with pytest.raises(ValueError, match="Unknown"):
        evaluate(arith(num(1), "XOR", num(2)))


def test_math_modulo_and_constrain():
    assert evaluate({"type": "math_modulo", "id": "m",
                     "DIVIDEND": num(17), "DIVISOR": num(5)}) == 2
    constrain = {"type": "math_constrain", "id": "c", "LOW": num(0), "HIGH": num(10)}
    assert evaluate({**constrain, "VALUE": num(-3)}) == 0
    assert evaluate({**constrain, "VALUE": num(4)}) == 4
    assert evaluate({**constrain, "VALUE": num(99)}) == 10


@pytest.mark.parametrize(("op", "value", "expected"), [
    ("ROUND", 2.5, 2), ("ROUND", 2.6, 3), ("ROUNDUP", 2.1, 3), ("ROUNDDOWN", 2.9, 2),
])
def test_math_round(op, value, expected):
    assert evaluate({"type": "math_round", "id": "r", "OP": op, "NUM": num(value)}) == expected


@pytest.mark.parametrize(("op", "expected"), [
    ("SUM", 12), ("MIN", 1), ("MAX", 5), ("AVERAGE", 3), ("MEDIAN", 3), ("MODE", [3]),
])
def test_math_on_list(op, expected):
    values = lst(num(1), num(3), num(3), num(5))
    assert evaluate({"type": "math_on_list", "id": "l", "OP": op, "LIST": values}) == expected


def test_math_on_list_without_list_sums_to_zero():
    assert evaluate({"type": "math_on_list", "id": "l", "OP": "SUM"}) == 0


# ---------------------------------------------------------------- logic

@pytest.mark.parametrize(("op", "expected"), [
    ("EQ", False), ("NEQ", True), ("LT", True), ("LTE", True), ("GT", False), ("GTE", False),
])
def test_logic_compare(op, expected):
    assert evaluate(compare(num(1), op, num(2))) is expected


def test_logic_compare_missing_inputs_compare_as_none():
    assert evaluate({"type": "logic_compare", "id": "c", "OP": "EQ"}) is True


@pytest.mark.parametrize(("op", "a", "b", "expected"), [
    ("AND", True, True, True), ("AND", True, False, False),
    ("OR", False, True, True), ("OR", False, False, False),
])
def test_logic_operation(op, a, b, expected):
    block = {"type": "logic_operation", "id": "o", "OP": op, "A": boolean(a), "B": boolean(b)}
    assert evaluate(block) is expected


def test_logic_negate_ternary_and_null():
    assert evaluate({"type": "logic_negate", "id": "n", "BOOL": boolean(True)}) is False
    assert evaluate({"type": "logic_negate", "id": "n"}) is True
    ternary = {"type": "logic_ternary", "id": "t", "THEN": txt("yes"), "ELSE": txt("no")}
    assert evaluate({**ternary, "IF": boolean(True)}) == "yes"
    assert evaluate({**ternary, "IF": boolean(False)}) == "no"
    assert evaluate({"type": "logic_null", "id": "z"}) is None


# ----------------------------------------------------------------- text

@pytest.mark.parametrize(("case", "expected"), [
    ("UPPERCASE", "HELLO WORLD"), ("LOWERCASE", "hello world"), ("TITLECASE", "Hello World"),
])
def test_text_change_case(case, expected):
    block = {"type": "text_changeCase", "id": "c", "CASE": case, "TEXT": txt("hEllo wOrld")}
    assert evaluate(block) == expected


@pytest.mark.parametrize(("mode", "expected"), [
    ("BOTH", "pad"), ("LEFT", "pad  "), ("RIGHT", "  pad"),
])
def test_text_trim(mode, expected):
    assert evaluate({"type": "text_trim", "id": "t", "MODE": mode, "TEXT": txt("  pad  ")}) == expected


@pytest.mark.parametrize(("where", "at", "expected"), [
    ("FROM_START", 2, "b"), ("FROM_END", 2, "d"), ("FIRST", None, "a"), ("LAST", None, "e"),
])
def test_text_char_at(where, at, expected):
    block = {"type": "text_charAt", "id": "c", "WHERE": where, "VALUE": txt("abcde")}
    if at is not None:
        block["AT"] = num(at)
    assert evaluate(block) == expected


def test_text_get_substring_one_based_inclusive():
    block = {"type": "text_getSubstring", "id": "s", "STRING": txt("abcdef"),
             "WHERE1": "FROM_START", "AT1": num(2), "WHERE2": "FROM_END", "AT2": num(2)}
    assert evaluate(block) == "bcde"
    block.update(WHERE1="FROM_END", AT1=num(3), WHERE2="FROM_END", AT2=num(1))
    assert evaluate(block) == "def"


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=(
    "BUG: text_getSubstring.Logic.init calls AT1/AT2.make_logic unconditionally, "
    "so FIRST/LAST (which have no AT input, default None) crash; lists_getSublist guards this"))
def test_text_get_substring_first_to_last_without_at_inputs():
    block = {"type": "text_getSubstring", "id": "s", "STRING": txt("abcdef"),
             "WHERE1": "FIRST", "WHERE2": "LAST"}
    assert evaluate(block) == "abcdef"


def test_text_index_of_and_join():
    index = {"type": "text_indexOf", "id": "i", "VALUE": txt("banana"), "FIND": txt("an")}
    assert evaluate({**index, "END": "FIRST"}) == 2
    assert evaluate({**index, "END": "LAST"}) == 4
    assert evaluate({**index, "END": "FIRST", "FIND": txt("x")}) == 0
    join = {"type": "text_join", "id": "j", "ADD1": num(2), "ADD0": txt("a"), "ADD2": txt("\u3042")}
    assert evaluate(join) == "a2\u3042"


# ---------------------------------------------------------------- lists

def test_lists_create_with_orders_items_and_fills_gaps():
    assert evaluate(lst(num(1), txt("x"))) == [1, "x"]
    assert evaluate({"type": "lists_create_with", "id": "l", "ADD2": num(3), "ADD0": num(1)}) == [1, None, 3]


@pytest.mark.parametrize(("type_", "direction", "expected"), [
    ("NUMERIC", "1", [2, 10, 33]),
    ("NUMERIC", "-1", [33, 10, 2]),
    ("TEXT", "1", [10, 2, 33]),
])
def test_lists_sort(type_, direction, expected):
    block = {"type": "lists_sort", "id": "s", "TYPE": type_, "DIRECTION": direction,
             "LIST": lst(num(10), num(2), num(33))}
    assert evaluate(block) == expected


def test_lists_sort_ignore_case():
    block = {"type": "lists_sort", "id": "s", "TYPE": "IGNORE_CASE", "DIRECTION": "1",
             "LIST": lst(txt("b"), txt("A"), txt("c"))}
    assert evaluate(block) == ["A", "b", "c"]


def test_lists_split_and_join():
    split = {"type": "lists_split", "id": "s", "MODE": "SPLIT", "INPUT": txt("a,b,c"), "DELIM": txt(",")}
    assert evaluate(split) == ["a", "b", "c"]
    join = {"type": "lists_split", "id": "s", "MODE": "JOIN", "INPUT": txt("abc"), "DELIM": txt("-")}
    assert evaluate(join) == "a-b-c"


@pytest.mark.parametrize(("where", "at", "expected"), [
    ("FROM_START", 1, "a"), ("FROM_START", 3, "c"), ("FROM_END", 1, "c"),
])
def test_lists_get_index(where, at, expected):
    block = {"type": "lists_getIndex_custom", "id": "g", "MODE": "GET", "WHERE": where,
             "AT": num(at), "VALUE": lst(txt("a"), txt("b"), txt("c"))}
    assert evaluate(block) == expected


def test_lists_get_sublist():
    base = {"type": "lists_getSublist", "id": "s", "LIST": lst(*(num(i) for i in range(1, 6)))}
    assert evaluate({**base, "WHERE1": "FROM_START", "AT1": num(2),
                     "WHERE2": "FROM_START", "AT2": num(4)}) == [2, 3, 4]
    assert evaluate({**base, "WHERE1": "FIRST", "WHERE2": "LAST"}) == [1, 2, 3, 4, 5]
    assert evaluate({**base, "WHERE1": "FROM_END", "AT1": num(2),
                     "WHERE2": "FROM_END", "AT2": num(1)}) == [4, 5]


def test_lists_repeat_list_item():
    block = {"type": "lists_repeat", "id": "r", "ITEM": lst(num(1)), "NUM": num(3)}
    assert evaluate(block) == [[1], [1], [1]]


@pytest.mark.xfail(strict=True, raises=TypeError, reason=(
    "BUG: lists_repeat.Logic.exec wraps ITEM in list(), so a scalar item raises "
    "TypeError (and a text item is split into characters) instead of being repeated"))
def test_lists_repeat_scalar_item():
    block = {"type": "lists_repeat", "id": "r", "ITEM": num(7), "NUM": num(2)}
    assert evaluate(block) == [7, 7]


# ----------------------------------------------------------------- dict

def test_dict_create_with_and_get_item():
    created = {"type": "dict_create_with", "id": "d",
               "KEY1": txt("b"), "VALUE1": num(2), "KEY0": txt("a"), "VALUE0": num(1), "KEY2": txt("c")}
    assert evaluate(created) == {"a": 1, "b": 2, "c": None}
    get = {"type": "dict_get_item", "id": "g", "MODE": "GET", "DICT": created, "KEY": txt("b")}
    assert evaluate(get) == 2
    assert evaluate({**get, "KEY": txt("zz")}) is None


# ------------------------------------------------------------ variables

def test_math_get_reads_job_variable(job_node):
    add_var(job_node, "x", value=41)
    assert evaluate(get_var("x")) == 41


def test_math_set_writes_job_variable(job_node):
    var = add_var(job_node, "x", value=1)
    run_statements(set_var("x", arith(get_var("x"), "MULTIPLY", num(10))))
    assert var.value == 10


def test_missing_variable_id_surfaces_as_runtime_error(job_node):
    with pytest.raises(RuntimeError, match="StopIteration"):
        evaluate(get_var("missing"))


# --------------------------------------------------- statements / command

def test_task_command_runs_chain_and_marks_finished(job_node):
    x = add_var(job_node, "x", 0)
    y = add_var(job_node, "y", 0)

    async def run():
        logic = await build(set_var("x", num(1), next=set_var("y", num(2)))).make_logic(JOB_ID, LOGGER)
        await command.Task(logic.domain.id).exec(logic, LOGGER)
        assert (x.value, y.value) == (1, 2)
        assert logic.domain.finished and logic.next.domain.finished
        x.value = 99
        await command.Task(logic.domain.id).exec(logic, LOGGER)
        assert x.value == 99
    asyncio.run(run())


def test_task_recover_resets_from_target_onwards(job_node):
    domain = build(set_var("x", num(1), id="a", next=set_var("x", num(2), id="b",
                                                             next=set_var("x", num(3), id="c"))))
    for d in (domain, domain.next, domain.next.next):
        d.finished = True
    assert command.Task("a").recover(domain, "b") is False
    assert [domain.finished, domain.next.finished, domain.next.next.finished] == [True, False, False]


def test_task_recover_rejects_unrecoverable_block():
    domain = build({"type": "controls_error", "id": "e", "error": txt("x")})
    with pytest.raises(Exception, match="cannot recover"):
        command.Task("e").recover(domain, "e")


def test_retrieve_task_finds_running_and_by_id(job_node):
    add_var(job_node, "x", 0)

    async def run():
        block = set_var("x", num(1), id="a", next=set_var("x", num(2), id="b",
                                                         next=set_var("x", num(3), id="c")))
        logic = await build(block).make_logic(JOB_ID, LOGGER)
        logic.domain.finished = True
        assert logic.retrieve_task().domain.id == "b"
        assert logic.retrieve_task("c").domain.id == "c"
        assert logic.retrieve_task("nope") is None
    asyncio.run(run())


def test_statement_default_exec_command_raises():
    async def run():
        logic = await build({"type": "controls_warning_clear", "id": "w"}).make_logic(JOB_ID, LOGGER)
        with pytest.raises(Exception, match="Failed to command"):
            await logic.exec_command("anything")
    asyncio.run(run())


# --------------------------------------------------------------- control

def if_block(*branches, else_=None, id="if"):
    block = {"type": "controls_if_custom", "id": id}
    for i, (cond, do) in enumerate(branches):
        block[f"IF{i}"] = cond
        block[f"DO{i}"] = do
    if else_ is not None:
        block["ELSE"] = else_
    return block


def test_controls_if_takes_first_true_branch(job_node):
    x = add_var(job_node, "x", 0)
    logic = run_statements(if_block(
        (compare(num(1), "EQ", num(2)), set_var("x", num(10), id="do0")),
        (boolean(True), set_var("x", num(20), id="do1")),
        else_=set_var("x", num(30), id="else"),
    ))
    assert x.value == 20
    assert logic.domain.command == [command.Task("do1")]


def test_controls_if_falls_back_to_else(job_node):
    x = add_var(job_node, "x", 0)
    run_statements(if_block((boolean(False), set_var("x", num(10), id="do0")),
                            else_=set_var("x", num(30), id="else")))
    assert x.value == 30


def test_controls_error_raises_and_shows_message():
    async def run():
        logic = await build({"type": "controls_error", "id": "e", "error": txt("boom")}).make_logic(JOB_ID, LOGGER)
        with pytest.raises(RuntimeError, match="boom"):
            await logic.exec()
        assert logic.domain.command == [command.Text("boom")]
    asyncio.run(run())


def test_controls_warning_and_clear(job_node):
    run_statements({"type": "controls_warning", "id": "w", "warning": txt("careful")})
    assert job_node.domain.warning_msg == {"careful"}
    run_statements({"type": "controls_warning_clear", "id": "wc"})
    assert job_node.domain.warning_msg == set()


def test_controls_try_runs_except_and_finally_then_reraises(job_node):
    handled = add_var(job_node, "handled", 0)
    cleaned = add_var(job_node, "cleaned", 0)
    block = {"type": "controls_try", "id": "try",
             "try_task": {"type": "controls_error", "id": "err", "error": txt("boom")},
             "except_task": set_var("handled", num(1), id="exc"),
             "finally_task": set_var("cleaned", num(1), id="fin")}
    with pytest.raises(RuntimeError, match="boom"):
        run_statements(block)
    assert (handled.value, cleaned.value) == (1, 1)


def test_job_result_raises_result_exception():
    with pytest.raises(job_exception.Result) as info:
        run_statements({"type": "job.active.result", "id": "r", "result": num(42)})
    assert info.value.args == (42,)
    with pytest.raises(job_exception.Result) as info:
        run_statements({"type": "job.active.result", "id": "r"})
    assert info.value.args == (None,)


# ----------------------------------------------------------------- loops

def test_flow_statement_raises_loop_signals():
    with pytest.raises(LoopBreak):
        run_statements({"type": "controls_flow_statements_custom", "id": "f", "FLOW": "BREAK"})
    with pytest.raises(LoopContinue):
        run_statements({"type": "controls_flow_statements_custom", "id": "f", "FLOW": "CONTINUE"})


def test_repeat_runs_body_n_times(job_node):
    x = add_var(job_node, "x", 0)
    logic = run_statements({"type": "controls_repeat_ext_custom", "id": "rep",
                            "TIMES": num(3), "DO": increment("x")})
    assert x.value == 3
    assert logic.domain.count == 3
    assert logic.domain.command == []


def test_repeat_break_from_nested_if(job_node):
    x = add_var(job_node, "x", 0)
    body = increment("x", next=if_block(
        (compare(get_var("x"), "EQ", num(3)),
         {"type": "controls_flow_statements_custom", "id": "brk", "FLOW": "BREAK"})))
    run_statements({"type": "controls_repeat_ext_custom", "id": "rep", "TIMES": num(10), "DO": body})
    assert x.value == 3


@pytest.mark.parametrize(("start", "end", "expected"), [(1, 4, 1234), (3, 1, 321)])
def test_for_loop_visits_inclusive_range(job_node, start, end, expected):
    add_var(job_node, "i")
    acc = add_var(job_node, "acc", 0)
    body = set_var("acc", arith(arith(get_var("acc"), "MULTIPLY", num(10)), "ADD", get_var("i")))
    run_statements({"type": "controls_for_custom", "id": "for", "VAR": {"id": "i"},
                    "FROM": num(start), "TO": num(end), "BY": num(1), "DO": body})
    assert acc.value == expected


@pytest.mark.parametrize(("mode", "cond", "expected"), [
    ("WHILE", ("LT", 3), 3),
    ("UNTIL", ("GTE", 2), 2),
])
def test_while_until(job_node, mode, cond, expected):
    x = add_var(job_node, "x", 0)
    run_statements({"type": "controls_whileUntil_custom", "id": "w", "MODE": mode,
                    "BOOL": compare(get_var("x"), cond[0], num(cond[1])), "DO": increment("x")})
    assert x.value == expected


def test_for_each_with_continue(job_node):
    add_var(job_node, "item")
    total = add_var(job_node, "total", 0)
    body = if_block((compare(get_var("item"), "EQ", num(2)),
                     {"type": "controls_flow_statements_custom", "id": "c", "FLOW": "CONTINUE"}),
                    id="skip")
    body["next"] = set_var("total", arith(get_var("total"), "ADD", get_var("item")))
    logic = run_statements({"type": "controls_forEach_custom", "id": "each", "VAR": {"id": "item"},
                            "LIST": lst(num(1), num(2), num(3), num(4)), "DO": body})
    assert total.value == 8
    assert logic.domain.count == 4


# ---------------------------------------------------------------- robot

@pytest.fixture
def robots(job_node):
    nodes = {}
    for name in ("r1", "r2", "r3"):
        node = object.__new__(robot.dummy.Node)
        node.domain = robot.dummy.NodeDomain(name=name, update_cycle=1.0)
        node.job = None
        repository.append(node)
        nodes[name] = node
    yield nodes
    for node in nodes.values():
        repository.remove(node)


def robot_ref(var_id="rv"):
    return {"type": "robot._get", "id": "rget", "VAR": {"id": var_id}}


def location(lat, lon):
    return {"type": "location_create", "id": "loc", "location": [lat, lon]}


def test_robot_get_resolves_variable_to_node(robots, job_node):
    var = add_var(job_node, "rv", "r2", type="Robot")
    assert evaluate(robot_ref()) is robots["r2"]
    var.value = None
    assert evaluate(robot_ref()) is None
    var.value = "ghost"
    with pytest.raises(Exception, match="ghost does not exist"):
        evaluate(robot_ref())


def test_is_dummy_and_get_domain(robots, job_node):
    var = add_var(job_node, "rv", "r1", type="Robot")
    assert evaluate({"type": "robot.dummy.is_dummy", "id": "d", "robot": robot_ref()}) is True
    assert evaluate({"type": "robot.get_domain", "id": "g", "robot": robot_ref(), "config": "update_cycle"}) == 1.0
    assert evaluate({"type": "robot.get_domain", "id": "g", "robot": robot_ref(), "config": "nope"}) is None
    var.value = None
    assert evaluate({"type": "robot.dummy.is_dummy", "id": "d", "robot": robot_ref()}) is False


def test_dummy_place_sets_location(robots, job_node):
    add_var(job_node, "rv", "r1", type="Robot")
    run_statements({"type": "robot.dummy.place", "id": "p", "robot": robot_ref(), "location": location(35.1, 137.2)})
    assert robots["r1"].domain.location == [35.1, 137.2]
    with pytest.raises(ValueError, match="Invalid coordinates"):
        run_statements({"type": "robot.dummy.place", "id": "p", "robot": robot_ref(), "location": location(91, 0)})


MOVE_LOGIC = importlib.import_module("src.job.task.robot.dummy.move.logic")


def test_move_geodesy_helpers():
    logic = object.__new__(MOVE_LOGIC.Logic)
    one_degree = MOVE_LOGIC.EARTH_RADIUS_M * math.pi / 180
    assert logic.haversine_distance_m(0, 0, 0, 1) == pytest.approx(one_degree)
    assert logic.initial_bearing_deg(0, 0, 0, 1) == pytest.approx(90)
    assert logic.initial_bearing_deg(0, 0, 1, 0) == pytest.approx(0)
    assert logic.initial_bearing_deg(0, 0, -1, 0) == pytest.approx(180)
    lat, lon = logic.destination_point(0, 0, 90, one_degree)
    assert (lat, lon) == (pytest.approx(0, abs=1e-9), pytest.approx(1))
    lat, lon = logic.destination_point(0, 179.5, 90, one_degree)
    assert lon == pytest.approx(-179.5)


def _patch_move_sleep(monkeypatch, hook=None):
    calls = []

    async def fake_sleep(delay):
        calls.append(delay)
        if hook:
            hook(len(calls))
    monkeypatch.setattr(MOVE_LOGIC, "asyncio", types.SimpleNamespace(sleep=fake_sleep))
    return calls


def test_dummy_move_reaches_target(robots, job_node, monkeypatch):
    add_var(job_node, "rv", "r1", type="Robot")
    robots["r1"].domain.location = [35.0, 137.0]
    calls = _patch_move_sleep(monkeypatch)
    logic = run_statements({"type": "robot.dummy.move", "id": "mv", "robot": robot_ref(),
                            "location": location(35.0, 137.001), "speed": num(36)})
    helper = object.__new__(MOVE_LOGIC.Logic)
    remaining = helper.haversine_distance_m(*robots["r1"].domain.location, 35.0, 137.001)
    assert remaining <= 1.0
    assert len(calls) == 10 and set(calls) == {1.0}
    assert logic.domain.command == []


def test_dummy_move_waits_while_stopped(robots, job_node, monkeypatch):
    add_var(job_node, "rv", "r1", type="Robot")
    halt = add_var(job_node, "halt", True)
    robots["r1"].domain.location = [35.0, 137.0]
    seen = []

    def hook(n):
        if n == 1:
            seen.append(list(robots["r1"].domain.location))
            halt.value = False
    _patch_move_sleep(monkeypatch, hook)
    run_statements({"type": "robot.dummy.move", "id": "mv", "robot": robot_ref(),
                    "location": location(35.0, 137.0001), "speed": num(36),
                    "stop": get_var("halt", kind="logic")})
    assert seen == [[35.0, 137.0]]
    assert robots["r1"].domain.location != [35.0, 137.0]


def test_dummy_move_rejects_invalid_target(robots, job_node, monkeypatch):
    add_var(job_node, "rv", "r1", type="Robot")
    robots["r1"].domain.location = [0.0, 0.0]
    _patch_move_sleep(monkeypatch)
    with pytest.raises(ValueError, match="Invalid coordinates"):
        run_statements({"type": "robot.dummy.move", "id": "mv", "robot": robot_ref(),
                        "location": location(0, 181), "speed": num(1)})


def select_block(condition=None):
    block = {"type": "robot.select", "id": "sel", "VAR": {"id": "rv"}}
    if condition is not None:
        block["condition"] = condition
    return block


def test_robot_select_offers_free_robots_and_binds_choice(robots, job_node):
    var = add_var(job_node, "rv", type="Robot")
    robots["r2"].job = object()

    async def run():
        logic = await build(select_block()).make_logic(JOB_ID, LOGGER)
        task = asyncio.create_task(logic.exec())
        for _ in range(5):
            await asyncio.sleep(0)
        offered = [c.label for c in logic.domain.command]
        with pytest.raises(Exception, match="r2"):
            await logic.exec_command("r2")
        await logic.exec_command("r3")
        await asyncio.wait_for(task, 1)
        return logic, offered

    logic, offered = asyncio.run(run())
    assert offered == ["r1", "r3"]
    assert robots["r3"].job is job_node
    assert var.value == "r3"
    assert logic.domain.command[-1].label.endswith("r3")


def test_robot_select_condition_filters_candidates(robots, job_node):
    var = add_var(job_node, "rv", type="Robot")
    condition = compare(get_var("rv", kind="text"), "EQ", txt("r2"))

    async def run():
        logic = await build(select_block(condition)).make_logic(JOB_ID, LOGGER)
        result = [await logic._can_select(robots[name]) for name in ("r1", "r2", "r3")]
        assert var.value is None
        with pytest.raises(Exception, match="Failed to command"):
            await logic.exec_command("ghost")
        return result

    assert asyncio.run(run()) == [False, True, False]
