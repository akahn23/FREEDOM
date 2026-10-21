# SPDX-License-Identifier: Apache-2.0

"""Tests for the /node/{node} RPC handler (src.freedom.user_interface.logic.Node.post)."""

import asyncio
import dataclasses
import datetime
import json
import sys
import types
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from aiohttp import web
from multidict import CIMultiDict
from src import freedom
from src.freedom.user_interface.logic import node as node_module

FAKE_NODE = "fake_ui_logic_target"


class FakeNode:
    """Stand-in node class exposed as src.<FAKE_NODE>.Node."""


@dataclasses.dataclass
class Payload:
    name: str
    at: datetime.datetime


@pytest.fixture
def fake_module(monkeypatch):
    module = types.ModuleType(f"src.{FAKE_NODE}")
    module.Node = FakeNode
    monkeypatch.setitem(sys.modules, f"src.{FAKE_NODE}", module)
    return module


@pytest.fixture
def logger():
    return MagicMock(name="logger")


@pytest.fixture
def repo(monkeypatch, logger):
    """Replace the module-level repository singleton.

    `repo.targets[cls]` is the list returned by `retrieve(cls, **domain)`.
    """
    log_node = MagicMock(name="log_node")
    log_node.make_logger.return_value = logger
    targets = {}

    def retrieve(cls, **kwargs):
        if cls is freedom.log.Node:
            return [log_node]
        return targets.get(cls, [])

    mock = MagicMock(name="repository")
    mock.retrieve.side_effect = retrieve
    mock.targets = targets
    mock.log_node = log_node
    monkeypatch.setattr(node_module, "repository", mock)
    return mock


@pytest.fixture
def fetch_allow_set(monkeypatch):
    mock = AsyncMock(name="fetch_allow_set", return_value={("robot.agv", "r1")})
    monkeypatch.setattr(node_module, "fetch_allow_set", mock)
    return mock


def make_request(node, body, headers=None, app=None):
    request = MagicMock(spec=web.Request)
    request.match_info = {"node": node}
    request.headers = CIMultiDict(headers or {})
    request.app = app if app is not None else {}
    request.json = AsyncMock(return_value=body)
    return request


def post(request):
    return asyncio.run(node_module.Node(request).post())


def make_auth_pool():
    conn = MagicMock(name="conn")
    pool = MagicMock(name="auth_pool")
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool, conn


# --- __init__ -------------------------------------------------------------


def test_init_creates_logger_from_log_node(repo, logger):
    view = node_module.Node(make_request(FAKE_NODE, {}))

    repo.retrieve.assert_called_once_with(freedom.log.Node)
    repo.log_node.make_logger.assert_called_once_with(node_module.__name__)
    assert view._logger is logger


def test_init_without_log_node_raises(monkeypatch):
    empty = MagicMock(name="repository")
    empty.retrieve.return_value = []
    monkeypatch.setattr(node_module, "repository", empty)

    with pytest.raises(IndexError):
        node_module.Node(make_request(FAKE_NODE, {}))


# --- happy path -----------------------------------------------------------


def test_post_resolves_node_and_calls_func(repo, fake_module):
    target = MagicMock(name="target")
    target.greet.return_value = {"hello": "world"}
    repo.targets[FakeNode] = [target]
    domain = {"group": "robot", "id": "r1"}

    resp = post(make_request(FAKE_NODE, {"domain": domain, "func": "greet", "kwargs": {"name": "x", "n": 2}}))

    assert resp.status == 200
    assert resp.content_type == "application/json"
    assert json.loads(resp.text) == {"hello": "world"}
    assert repo.retrieve.call_args_list[-1] == call(FakeNode, group="robot", id="r1")
    target.greet.assert_called_once_with(name="x", n=2)


def test_post_uses_first_retrieved_instance(repo, fake_module):
    first, second = MagicMock(name="first"), MagicMock(name="second")
    first.ping.return_value = "first"
    second.ping.return_value = "second"
    repo.targets[FakeNode] = [first, second]

    resp = post(make_request(FAKE_NODE, {"func": "ping"}))

    assert json.loads(resp.text) == "first"
    second.ping.assert_not_called()


def test_post_defaults_domain_and_kwargs_to_empty(repo, fake_module):
    target = MagicMock(name="target")
    target.ping.return_value = None
    repo.targets[FakeNode] = [target]

    resp = post(make_request(FAKE_NODE, {"func": "ping"}))

    assert resp.status == 200
    assert resp.text == "null"
    assert repo.retrieve.call_args_list[-1] == call(FakeNode)
    target.ping.assert_called_once_with()


def test_post_imports_node_module_from_match_info(repo):
    """Real module path: /node/freedom.map resolves src.freedom.map.Node."""
    target = MagicMock(name="map")
    target.fetch_node.return_value = ["a"]
    repo.targets[freedom.map.Node] = [target]

    resp = post(make_request("freedom.map", {"func": "fetch_node"}))

    assert json.loads(resp.text) == ["a"]
    assert repo.retrieve.call_args_list[-1] == call(freedom.map.Node)


def test_post_serializes_with_util_json_dumps(repo, fake_module, monkeypatch):
    real_dumps = node_module.util.json.dumps
    dumps = MagicMock(name="dumps", side_effect=real_dumps)
    monkeypatch.setattr(node_module.util.json, "dumps", dumps)
    result = {
        "payload": Payload("p", datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=datetime.UTC)),
        "ids": {"only"},
        "day": datetime.date(2026, 1, 2),
    }
    target = MagicMock(name="target")
    target.get.return_value = result
    repo.targets[FakeNode] = [target]

    resp = post(make_request(FAKE_NODE, {"func": "get"}))

    dumps.assert_called_once_with(result)
    assert json.loads(resp.text) == {
        "payload": {"name": "p", "at": "2026-01-02T03:04:05+00:00"},
        "ids": ["only"],
        "day": "2026-01-02",
    }


# --- coroutine results ----------------------------------------------------


def test_post_awaits_coroutine_result(repo, fake_module):
    calls = []

    class Target:
        async def compute(self, x):
            await asyncio.sleep(0)
            calls.append(x)
            return {"double": x * 2}

    repo.targets[FakeNode] = [Target()]

    resp = post(make_request(FAKE_NODE, {"func": "compute", "kwargs": {"x": 21}}))

    assert resp.status == 200
    assert json.loads(resp.text) == {"double": 42}
    assert calls == [21]


def test_post_awaits_async_mock_method(repo, fake_module):
    target = MagicMock(name="target")
    target.run = AsyncMock(return_value=[1, 2])
    repo.targets[FakeNode] = [target]

    resp = post(make_request(FAKE_NODE, {"func": "run", "kwargs": {"a": 1}}))

    assert json.loads(resp.text) == [1, 2]
    target.run.assert_awaited_once_with(a=1)


# --- errors ---------------------------------------------------------------


def test_post_sync_exception_returns_500_with_message(repo, fake_module, logger):
    target = MagicMock(name="target")
    target.fail.side_effect = ValueError("boom")
    repo.targets[FakeNode] = [target]
    body = {"func": "fail"}

    resp = post(make_request(FAKE_NODE, body))

    assert resp.status == 500
    assert resp.text == "boom"
    logger.error.assert_called_once()
    message = logger.error.call_args.args[0]
    assert "ValueError" in message
    assert f"node={FAKE_NODE}" in message
    assert f"body={body!r}" in message


def test_post_coroutine_exception_returns_500_with_message(repo, fake_module, logger):
    target = MagicMock(name="target")
    target.fail = AsyncMock(side_effect=RuntimeError("async boom"))
    repo.targets[FakeNode] = [target]

    resp = post(make_request(FAKE_NODE, {"func": "fail"}))

    assert resp.status == 500
    assert resp.text == "async boom"
    logger.error.assert_called_once()


def test_post_missing_func_returns_500(repo, fake_module):
    resp = post(make_request(FAKE_NODE, {"kwargs": {}}))

    assert resp.status == 500
    assert resp.text == "'func'"


def test_post_no_matching_instance_returns_500(repo, fake_module):
    resp = post(make_request(FAKE_NODE, {"domain": {"id": "missing"}, "func": "ping"}))

    assert resp.status == 500
    assert resp.text == "list index out of range"


def test_post_unknown_func_returns_500(repo, fake_module):
    class Target:
        pass

    repo.targets[FakeNode] = [Target()]

    resp = post(make_request(FAKE_NODE, {"func": "nope"}))

    assert resp.status == 500
    assert "nope" in resp.text


def test_post_unexpected_kwargs_returns_500(repo, fake_module):
    class Target:
        def ping(self):
            return "pong"

    repo.targets[FakeNode] = [Target()]

    resp = post(make_request(FAKE_NODE, {"func": "ping", "kwargs": {"extra": 1}}))

    assert resp.status == 500
    assert "extra" in resp.text


@pytest.mark.xfail(
    strict=True,
    raises=UnboundLocalError,
    reason="Latent bug: the except block logs `body` before it is assigned, "
    "so an unknown node module raises UnboundLocalError instead of a 500 response",
)
def test_post_unknown_node_module_returns_500(repo):
    resp = post(make_request("no_such_repository.no_such_node", {"func": "ping"}))

    assert resp.status == 500
    assert "no_such_repository" in resp.text


@pytest.mark.xfail(
    strict=True,
    raises=UnboundLocalError,
    reason="Latent bug: the except block logs `body` before it is assigned, "
    "so an invalid JSON body raises UnboundLocalError instead of a 500 response",
)
def test_post_invalid_json_body_returns_500(repo, fake_module):
    request = make_request(FAKE_NODE, None)
    request.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)

    resp = post(request)

    assert resp.status == 500


# --- freedom.map + fetch_status special case ------------------------------


@pytest.fixture
def map_node(repo):
    target = MagicMock(name="map")
    target.fetch_status.return_value = [{"name": "lamp_1"}]
    repo.targets[freedom.map.Node] = [target]
    return target


def test_fetch_status_admin_sets_allow_set_none(map_node, fetch_allow_set):
    resp = post(make_request(
        "freedom.map",
        {"func": "fetch_status", "kwargs": {"node_name": "lamp_1"}},
        headers={"x-user-role": "admin", "x-user-id": "u1"},
        app={"auth_pool": make_auth_pool()[0]},
    ))

    assert resp.status == 200
    assert json.loads(resp.text) == [{"name": "lamp_1"}]
    map_node.fetch_status.assert_called_once_with(node_name="lamp_1", allow_set=None)
    fetch_allow_set.assert_not_called()


def test_fetch_status_admin_overrides_client_allow_set(map_node):
    post(make_request(
        "freedom.map",
        {"func": "fetch_status", "kwargs": {"allow_set": [["robot.agv", "r1"]]}},
        headers={"x-user-role": "admin"},
    ))

    map_node.fetch_status.assert_called_once_with(allow_set=None)


def test_fetch_status_user_without_auth_pool_gets_empty_set(map_node, fetch_allow_set):
    resp = post(make_request(
        "freedom.map",
        {"func": "fetch_status"},
        headers={"x-user-id": "u1", "x-user-role": "user"},
    ))

    assert resp.status == 200
    map_node.fetch_status.assert_called_once_with(allow_set=set())
    fetch_allow_set.assert_not_called()


def test_fetch_status_user_overrides_client_allow_set(map_node):
    post(make_request(
        "freedom.map",
        {"func": "fetch_status", "kwargs": {"allow_set": None}},
        headers={"x-user-id": "u1"},
    ))

    map_node.fetch_status.assert_called_once_with(allow_set=set())


def test_fetch_status_user_with_auth_pool_uses_fetch_allow_set(map_node, fetch_allow_set):
    pool, conn = make_auth_pool()

    resp = post(make_request(
        "freedom.map",
        {"func": "fetch_status"},
        headers={"x-user-id": "u1", "x-user-role": "user"},
        app={"auth_pool": pool},
    ))

    assert resp.status == 200
    fetch_allow_set.assert_awaited_once_with(conn, "u1")
    pool.acquire.assert_called_once_with()
    pool.acquire.return_value.__aexit__.assert_called_once()
    map_node.fetch_status.assert_called_once_with(allow_set={("robot.agv", "r1")})


def test_fetch_status_fetch_allow_set_error_returns_500(map_node, fetch_allow_set):
    fetch_allow_set.side_effect = RuntimeError("db down")

    resp = post(make_request(
        "freedom.map",
        {"func": "fetch_status"},
        headers={"x-user-id": "u1"},
        app={"auth_pool": make_auth_pool()[0]},
    ))

    assert resp.status == 500
    assert resp.text == "db down"
    map_node.fetch_status.assert_not_called()


def test_fetch_status_anonymous_leaves_kwargs_untouched(map_node, fetch_allow_set):
    post(make_request("freedom.map", {"func": "fetch_status", "kwargs": {"node_name": "x"}}))

    map_node.fetch_status.assert_called_once_with(node_name="x")
    fetch_allow_set.assert_not_called()


def test_fetch_status_role_is_case_sensitive(map_node):
    post(make_request(
        "freedom.map",
        {"func": "fetch_status"},
        headers={"x-user-role": "Admin", "x-user-id": "u1"},
    ))

    map_node.fetch_status.assert_called_once_with(allow_set=set())


def test_other_map_func_is_not_special_cased(map_node):
    map_node.fetch_node.return_value = []

    post(make_request(
        "freedom.map",
        {"func": "fetch_node"},
        headers={"x-user-role": "admin", "x-user-id": "u1"},
    ))

    map_node.fetch_node.assert_called_once_with()


def test_fetch_status_on_other_node_is_not_special_cased(repo, fake_module):
    target = MagicMock(name="target")
    target.fetch_status.return_value = []
    repo.targets[FakeNode] = [target]

    post(make_request(
        FAKE_NODE,
        {"func": "fetch_status"},
        headers={"x-user-role": "admin", "x-user-id": "u1"},
    ))

    target.fetch_status.assert_called_once_with()
