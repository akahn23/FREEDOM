import asyncio
import dataclasses
import json
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from multidict import CIMultiDict

from src import freedom
from src.freedom.user_interface.logic import domain as logic_domain
from src.freedom.user_interface.logic import node as logic_node
from src.repository import Repository

FAKE_NODE = "fake_ui_logic"
FAKE_MODULE = f"src.{FAKE_NODE}"
MISSING_NODE = "no_such_repository.no_such_node"


@dataclasses.dataclass
class FakeDomain:
    name: str
    group: str = "robot"


class FakeNode:
    def __init__(self, name, group="robot"):
        self.domain = FakeDomain(name=name, group=group)
        self.calls = []

    def echo(self, **kwargs):
        self.calls.append(("echo", kwargs))
        return {"node": self.domain.name, "kwargs": kwargs}

    async def echo_async(self, **kwargs):
        await asyncio.sleep(0)
        self.calls.append(("echo_async", kwargs))
        return {"node": self.domain.name, "kwargs": kwargs, "awaited": True}

    def fail(self):
        raise ValueError("sync failure")

    async def fail_async(self):
        raise RuntimeError("async failure")


class FakeMapNode(freedom.map.Node):
    def __init__(self, name="map"):
        self.domain = FakeDomain(name=name, group="freedom")
        self.calls = []

    def fetch_status(self, node_name=None, **kwargs):
        self.calls.append(("fetch_status", {"node_name": node_name, **kwargs}))
        return {"node_name": node_name, "has_allow_set": "allow_set" in kwargs}

    def fetch_structure(self, **kwargs):
        self.calls.append(("fetch_structure", kwargs))
        return "structure"


class FakePool:
    def __init__(self, conn):
        self.conn = conn
        self.acquired = 0
        self.released = 0

    def acquire(self):
        pool = self

        class _Ctx:
            async def __aenter__(self):
                pool.acquired += 1
                return pool.conn

            async def __aexit__(self, *exc):
                pool.released += 1
                return False

        return _Ctx()


def make_log_node():
    log_node = object.__new__(freedom.log.Node)
    logger = MagicMock(name="logger")
    log_node.make_logger = MagicMock(return_value=logger)
    return log_node, logger


@pytest.fixture
def logger_and_repo(monkeypatch):
    log_node, logger = make_log_node()
    repo = Repository([log_node])
    monkeypatch.setattr(logic_node, "repository", repo)
    monkeypatch.setattr(logic_domain, "repository", repo)
    return logger, repo


@pytest.fixture
def repo(logger_and_repo):
    return logger_and_repo[1]


@pytest.fixture
def logger(logger_and_repo):
    return logger_and_repo[0]


@pytest.fixture
def fake_nodes(monkeypatch, repo):
    module = types.ModuleType(FAKE_MODULE)
    module.Node = FakeNode
    monkeypatch.setitem(sys.modules, FAKE_MODULE, module)
    nodes = [FakeNode("robot_1"), FakeNode("robot_2"), FakeNode("lamp_1", group="infrastructure")]
    repo.extend(nodes)
    return nodes


@pytest.fixture
def map_node(repo):
    node = FakeMapNode()
    repo.append(node)
    return node


def make_request(node, body=None, headers=None, app=None, can_read_body=True, json_error=None):
    request = MagicMock(spec=web.Request)
    request.match_info = {"node": node}
    request.headers = CIMultiDict(headers or {})
    request.app = {} if app is None else app
    request.can_read_body = can_read_body
    if json_error is not None:
        request.json = AsyncMock(side_effect=json_error)
    else:
        request.json = AsyncMock(return_value=body)
    return request


def post_node(request):
    return asyncio.run(logic_node.Node(request).post())


def post_domain(request):
    return asyncio.run(logic_domain.Domain(request).post())


def body_of(response):
    return json.loads(response.text)


# ---------------------------------------------------------------------------
# Node.post: dispatch
# ---------------------------------------------------------------------------


def test_node_init_makes_logger_from_log_node(repo, logger):
    log_node = repo[0]
    view = logic_node.Node(make_request(FAKE_NODE, body={}))
    log_node.make_logger.assert_called_once_with(logic_node.__name__)
    assert view._logger is logger


def test_node_post_calls_sync_method_with_kwargs(fake_nodes):
    body = {"domain": {"name": "robot_2"}, "func": "echo", "kwargs": {"a": 1, "b": "x"}}
    response = post_node(make_request(FAKE_NODE, body=body))
    assert response.status == 200
    assert response.content_type == "application/json"
    assert body_of(response) == {"node": "robot_2", "kwargs": {"a": 1, "b": "x"}}
    assert fake_nodes[1].calls == [("echo", {"a": 1, "b": "x"})]
    assert fake_nodes[0].calls == []
    assert fake_nodes[2].calls == []


def test_node_post_awaits_coroutine_method(fake_nodes):
    body = {"domain": {"name": "robot_1"}, "func": "echo_async", "kwargs": {"x": [1, 2]}}
    response = post_node(make_request(FAKE_NODE, body=body))
    assert response.status == 200
    assert body_of(response) == {"node": "robot_1", "kwargs": {"x": [1, 2]}, "awaited": True}
    assert fake_nodes[0].calls == [("echo_async", {"x": [1, 2]})]


def test_node_post_defaults_domain_and_kwargs(fake_nodes):
    response = post_node(make_request(FAKE_NODE, body={"func": "echo"}))
    assert response.status == 200
    assert body_of(response) == {"node": "robot_1", "kwargs": {}}
    assert fake_nodes[0].calls == [("echo", {})]


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        ({"name": "lamp_1"}, 2),
        ({"group": "infrastructure"}, 2),
        ({"group": "robot", "name": "robot_2"}, 1),
        ({"group": "robot"}, 0),
    ],
)
def test_node_post_domain_filter_selects_first_matching_node(fake_nodes, domain, expected):
    response = post_node(make_request(FAKE_NODE, body={"domain": domain, "func": "echo"}))
    assert response.status == 200
    assert body_of(response)["node"] == fake_nodes[expected].domain.name
    called = [i for i, n in enumerate(fake_nodes) if n.calls]
    assert called == [expected]


def test_node_post_ignores_nodes_of_other_classes(fake_nodes, map_node):
    response = post_node(make_request(FAKE_NODE, body={"domain": {"name": "map"}, "func": "echo"}))
    assert response.status == 500
    assert response.text == "list index out of range"
    assert map_node.calls == []


def test_node_post_serializes_result_with_util_json(fake_nodes, monkeypatch):
    monkeypatch.setattr(FakeNode, "echo", lambda self, **kw: {"domain": self.domain, "tags": {"a"}})
    response = post_node(make_request(FAKE_NODE, body={"domain": {"name": "robot_1"}, "func": "echo"}))
    assert response.status == 200
    assert body_of(response) == {"domain": {"name": "robot_1", "group": "robot"}, "tags": ["a"]}


# ---------------------------------------------------------------------------
# Node.post: allow_set resolution for freedom.map.fetch_status
# ---------------------------------------------------------------------------


@pytest.fixture
def allow_set_spy(monkeypatch):
    spy = AsyncMock(return_value={("robot.dummy", "robot_1")})
    monkeypatch.setattr(logic_node, "fetch_allow_set", spy)
    return spy


def fetch_status_request(headers=None, app=None, func="fetch_status", kwargs=None):
    body = {"func": func, "kwargs": {"node_name": "robot_1"} if kwargs is None else kwargs}
    return make_request("freedom.map", body=body, headers=headers, app=app)


def test_fetch_status_admin_gets_allow_set_none(map_node, allow_set_spy):
    response = post_node(fetch_status_request(headers={"x-user-role": "admin"}))
    assert response.status == 200
    assert map_node.calls == [("fetch_status", {"node_name": "robot_1", "allow_set": None})]
    allow_set_spy.assert_not_called()


def test_fetch_status_admin_wins_over_user_id_and_pool(map_node, allow_set_spy):
    pool = FakePool(conn=object())
    request = fetch_status_request(
        headers={"x-user-id": "u1", "X-User-Role": "admin"}, app={"auth_pool": pool}
    )
    response = post_node(request)
    assert response.status == 200
    assert map_node.calls == [("fetch_status", {"node_name": "robot_1", "allow_set": None})]
    allow_set_spy.assert_not_called()
    assert pool.acquired == 0


def test_fetch_status_admin_overrides_client_supplied_allow_set(map_node, allow_set_spy):
    request = fetch_status_request(
        headers={"x-user-role": "admin"}, kwargs={"allow_set": [["robot.dummy", "x"]]}
    )
    post_node(request)
    assert map_node.calls == [("fetch_status", {"node_name": None, "allow_set": None})]


def test_fetch_status_user_with_pool_uses_fetch_allow_set(map_node, allow_set_spy):
    conn = object()
    pool = FakePool(conn)
    request = fetch_status_request(
        headers={"x-user-id": "user-42", "x-user-role": "viewer"}, app={"auth_pool": pool}
    )
    response = post_node(request)
    assert response.status == 200
    allow_set_spy.assert_awaited_once_with(conn, "user-42")
    assert pool.acquired == 1
    assert pool.released == 1
    assert map_node.calls == [
        ("fetch_status", {"node_name": "robot_1", "allow_set": {("robot.dummy", "robot_1")}})
    ]


def test_fetch_status_fetch_allow_set_error_returns_500(map_node, monkeypatch):
    monkeypatch.setattr(logic_node, "fetch_allow_set", AsyncMock(side_effect=ConnectionError("db down")))
    pool = FakePool(conn=object())
    response = post_node(fetch_status_request(headers={"x-user-id": "u1"}, app={"auth_pool": pool}))
    assert response.status == 500
    assert response.text == "db down"
    assert pool.released == 1
    assert map_node.calls == []


def test_fetch_status_user_without_pool_gets_empty_set(map_node, allow_set_spy):
    response = post_node(fetch_status_request(headers={"x-user-id": "user-42"}))
    assert response.status == 200
    assert map_node.calls == [("fetch_status", {"node_name": "robot_1", "allow_set": set()})]
    allow_set_spy.assert_not_called()


def test_fetch_status_without_headers_does_not_inject_allow_set(map_node, allow_set_spy):
    response = post_node(fetch_status_request(app={"auth_pool": FakePool(object())}))
    assert response.status == 200
    assert body_of(response) == {"node_name": "robot_1", "has_allow_set": False}
    assert map_node.calls == [("fetch_status", {"node_name": "robot_1"})]
    allow_set_spy.assert_not_called()


def test_fetch_status_non_admin_role_without_user_id_does_not_inject(map_node, allow_set_spy):
    post_node(fetch_status_request(headers={"x-user-role": "viewer"}))
    assert map_node.calls == [("fetch_status", {"node_name": "robot_1"})]


def test_other_map_func_does_not_inject_allow_set(map_node, allow_set_spy):
    request = fetch_status_request(
        headers={"x-user-id": "u1", "x-user-role": "admin"},
        app={"auth_pool": FakePool(object())},
        func="fetch_structure",
        kwargs={},
    )
    response = post_node(request)
    assert response.status == 200
    assert body_of(response) == "structure"
    assert map_node.calls == [("fetch_structure", {})]
    allow_set_spy.assert_not_called()


def test_fetch_status_on_other_node_does_not_inject_allow_set(fake_nodes, allow_set_spy, monkeypatch):
    monkeypatch.setattr(FakeNode, "fetch_status", FakeNode.echo, raising=False)
    request = make_request(
        FAKE_NODE,
        body={"func": "fetch_status", "kwargs": {"q": 1}},
        headers={"x-user-id": "u1", "x-user-role": "admin"},
        app={"auth_pool": FakePool(object())},
    )
    response = post_node(request)
    assert response.status == 200
    assert fake_nodes[0].calls == [("echo", {"q": 1})]
    allow_set_spy.assert_not_called()


# ---------------------------------------------------------------------------
# Node.post: errors
# ---------------------------------------------------------------------------


def test_node_post_unknown_func_returns_500(fake_nodes, logger):
    response = post_node(make_request(FAKE_NODE, body={"func": "does_not_exist"}))
    assert response.status == 500
    assert response.text == "'FakeNode' object has no attribute 'does_not_exist'"
    logger.error.assert_called_once()
    assert "AttributeError" in logger.error.call_args.args[0]


def test_node_post_missing_func_returns_500(fake_nodes):
    response = post_node(make_request(FAKE_NODE, body={"kwargs": {}}))
    assert response.status == 500
    assert response.text == "'func'"


def test_node_post_no_matching_domain_returns_500(fake_nodes):
    response = post_node(make_request(FAKE_NODE, body={"domain": {"name": "ghost"}, "func": "echo"}))
    assert response.status == 500
    assert response.text == "list index out of range"
    assert all(n.calls == [] for n in fake_nodes)


def test_node_post_bad_kwargs_returns_500(fake_nodes):
    response = post_node(make_request(FAKE_NODE, body={"func": "fail", "kwargs": {"x": 1}}))
    assert response.status == 500
    assert "unexpected keyword argument 'x'" in response.text


def test_node_post_sync_exception_returns_500(fake_nodes):
    response = post_node(make_request(FAKE_NODE, body={"func": "fail"}))
    assert response.status == 500
    assert response.text == "sync failure"


def test_node_post_coroutine_exception_returns_500(fake_nodes):
    response = post_node(make_request(FAKE_NODE, body={"func": "fail_async"}))
    assert response.status == 500
    assert response.text == "async failure"


def test_node_post_unserializable_result_returns_500(fake_nodes, monkeypatch):
    monkeypatch.setattr(FakeNode, "echo", lambda self, **kw: object())
    response = post_node(make_request(FAKE_NODE, body={"func": "echo"}))
    assert response.status == 500
    assert "not JSON serializable" in response.text


@pytest.mark.xfail(
    strict=True,
    raises=UnboundLocalError,
    reason="logic/node.py: except block logs `body` before it is assigned when the node "
    "module import fails, so UnboundLocalError escapes instead of a 500 with str(e)",
)
def test_node_post_unknown_node_returns_500(repo):
    response = post_node(make_request(MISSING_NODE, body={"func": "echo"}))
    assert response.status == 500
    assert "no_such_repository" in response.text


@pytest.mark.xfail(
    strict=True,
    raises=UnboundLocalError,
    reason="logic/node.py: except block logs `body` before it is assigned when "
    "request.json() fails, so UnboundLocalError escapes instead of a 500 with str(e)",
)
def test_node_post_invalid_json_returns_500(fake_nodes):
    error = json.JSONDecodeError("Expecting value", "not json", 0)
    response = post_node(make_request(FAKE_NODE, json_error=error))
    assert response.status == 500
    assert "Expecting value" in response.text


# ---------------------------------------------------------------------------
# Domain.post
# ---------------------------------------------------------------------------


def test_domain_init_makes_logger_from_log_node(repo, logger):
    view = logic_domain.Domain(make_request(FAKE_NODE, body={}))
    repo[0].make_logger.assert_called_once_with(logic_domain.__name__)
    assert view._logger is logger


def test_domain_post_returns_matching_domains(fake_nodes):
    response = post_domain(make_request(FAKE_NODE, body={"group": "robot"}))
    assert response.status == 200
    assert body_of(response) == [
        {"name": "robot_1", "group": "robot"},
        {"name": "robot_2", "group": "robot"},
    ]


def test_domain_post_empty_body_returns_all_domains(fake_nodes):
    response = post_domain(make_request(FAKE_NODE, body={}))
    assert response.status == 200
    assert [d["name"] for d in body_of(response)] == ["robot_1", "robot_2", "lamp_1"]


def test_domain_post_unreadable_body_returns_all_domains(fake_nodes):
    request = make_request(FAKE_NODE, can_read_body=False, json_error=AssertionError("must not read"))
    response = post_domain(request)
    assert response.status == 200
    assert [d["name"] for d in body_of(response)] == ["robot_1", "robot_2", "lamp_1"]
    request.json.assert_not_called()


def test_domain_post_no_match_returns_empty_list(fake_nodes):
    response = post_domain(make_request(FAKE_NODE, body={"name": "ghost"}))
    assert response.status == 200
    assert body_of(response) == []


def test_domain_post_only_returns_nodes_of_requested_class(fake_nodes, map_node):
    response = post_domain(make_request("freedom.map", body={}))
    assert response.status == 200
    assert body_of(response) == [{"name": "map", "group": "freedom"}]


def test_domain_post_error_returns_500_with_type_and_message(fake_nodes, monkeypatch, logger):
    def boom(self, cls, **kwargs):
        raise ValueError("retrieve failed")

    monkeypatch.setattr(Repository, "retrieve", boom)
    request = make_request(FAKE_NODE, body={"name": "robot_1"})
    view = logic_domain.Domain.__new__(logic_domain.Domain)
    web.View.__init__(view, request)
    view._logger = logger
    response = asyncio.run(view.post())
    assert response.status == 500
    assert response.text == "<class 'ValueError'> - retrieve failed"
    logger.error.assert_called_once()


def test_domain_post_non_dict_body_returns_500(fake_nodes):
    response = post_domain(make_request(FAKE_NODE, body=["robot_1"]))
    assert response.status == 500
    assert response.text.startswith("<class 'TypeError'> - ")


@pytest.mark.xfail(
    strict=True,
    raises=UnboundLocalError,
    reason="logic/domain.py: except block logs `body` before it is assigned when the node "
    "module import fails, so UnboundLocalError escapes instead of a 500 with the message",
)
def test_domain_post_unknown_node_returns_500(repo):
    response = post_domain(make_request(MISSING_NODE, body={}))
    assert response.status == 500
    assert response.text.startswith("<class 'ModuleNotFoundError'> - ")


@pytest.mark.xfail(
    strict=True,
    raises=UnboundLocalError,
    reason="logic/domain.py: except block logs `body` before it is assigned when "
    "request.json() fails, so UnboundLocalError escapes instead of a 500 with the message",
)
def test_domain_post_invalid_json_returns_500(fake_nodes):
    error = json.JSONDecodeError("Expecting value", "not json", 0)
    response = post_domain(make_request(FAKE_NODE, json_error=error))
    assert response.status == 500
    assert response.text.startswith("<class 'json.decoder.JSONDecodeError'> - ")
