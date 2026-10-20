import dataclasses
import sys
import types
from datetime import datetime

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from src import freedom
from src.freedom.user_interface import logic
from src.repository import repository

FAKE_MODULE = "tests_fake_robot"


@dataclasses.dataclass
class FakeDomain:
    id: str
    group: str = "robot"


@dataclasses.dataclass
class Pose:
    x: float
    at: datetime


class FakeNode:
    def __init__(self, id:str):
        self.domain = FakeDomain(id)
        self.calls = []

    def ping(self):
        return f"pong:{self.domain.id}"

    def move(self, x:float, at:str):
        self.calls.append(("move", x, at))
        return Pose(x, datetime.fromisoformat(at))

    async def recover(self, reason:str="manual"):
        self.calls.append(("recover", reason))
        return {"recovered": self.domain.id, "reason": reason}

    def explode(self):
        raise RuntimeError("robot is offline")


class FakeMapNode:
    def __init__(self):
        self.domain = FakeDomain("map", group="freedom")
        self.allow_sets = []

    def fetch_status(self, allow_set="unset"):
        self.allow_sets.append(allow_set)
        return []


class FakeAuthPool:
    def __init__(self, rows):
        self.conn = types.SimpleNamespace(fetch=self._fetch)
        self.rows = rows
        self.queries = []

    async def _fetch(self, sql, *args):
        self.queries.append((sql, args))
        return self.rows

    def acquire(self):
        pool = self

        class _Ctx:
            async def __aenter__(self):
                return pool.conn

            async def __aexit__(self, *exc):
                return False

        return _Ctx()


@pytest.fixture
def fake_module(monkeypatch):
    module = types.ModuleType(f"src.{FAKE_MODULE}")
    module.Node = FakeNode
    monkeypatch.setitem(sys.modules, f"src.{FAKE_MODULE}", module)
    return module


@pytest.fixture
def robots(fake_log_node, fake_module):
    nodes = [FakeNode("r1"), FakeNode("r2")]
    repository.extend(nodes)
    return nodes


@pytest.fixture
def map_node(fake_log_node, monkeypatch):
    monkeypatch.setattr(freedom.map, "Node", FakeMapNode)
    node = FakeMapNode()
    repository.append(node)
    return node


@pytest.fixture
async def make_client():
    clients = []

    async def _make(auth_pool=None):
        app = web.Application()
        app.router.add_view("/node/{node}", logic.Node)
        app.router.add_view("/domain/{node}", logic.Domain)
        if auth_pool is not None:
            app["auth_pool"] = auth_pool
        client = TestClient(TestServer(app))
        await client.start_server()
        clients.append(client)
        return client

    yield _make
    for client in clients:
        await client.close()


# --- node dispatch -----------------------------------------------------------

async def test_dispatches_to_node_selected_by_domain(robots, make_client):
    client = await make_client()

    resp = await client.post(f"/node/{FAKE_MODULE}", json={"domain": {"id": "r2"}, "func": "ping"})

    assert resp.status == 200
    assert await resp.json() == "pong:r2"


async def test_without_domain_uses_first_registered_node(robots, make_client):
    client = await make_client()

    resp = await client.post(f"/node/{FAKE_MODULE}", json={"func": "ping"})

    assert await resp.json() == "pong:r1"


async def test_passes_kwargs_and_serializes_with_custom_json(robots, make_client):
    client = await make_client()

    resp = await client.post(f"/node/{FAKE_MODULE}", json={
        "domain": {"id": "r1"}, "func": "move", "kwargs": {"x": 1.5, "at": "2026-01-01T00:00:00+00:00"},
    })

    assert resp.status == 200
    body = await resp.json()
    assert body["x"] == 1.5
    assert body["at"].startswith("2026-01-01")
    assert robots[0].calls == [("move", 1.5, "2026-01-01T00:00:00+00:00")]
    assert robots[1].calls == []


async def test_awaits_coroutine_methods(robots, make_client):
    client = await make_client()

    resp = await client.post(f"/node/{FAKE_MODULE}", json={"func": "recover", "kwargs": {"reason": "e-stop"}})

    assert await resp.json() == {"recovered": "r1", "reason": "e-stop"}


@pytest.mark.parametrize(("body", "message"), [
    ({"func": "explode"}, "robot is offline"),
    ({"func": "no_such_method"}, "no_such_method"),
    ({"domain": {"id": "missing"}, "func": "ping"}, "list index out of range"),
    ({"kwargs": {}}, "'func'"),
    ({"func": "ping", "kwargs": {"bogus": 1}}, "bogus"),
])
async def test_errors_become_500_with_message_and_are_logged(robots, fake_log_node, make_client, body, message):
    client = await make_client()

    resp = await client.post(f"/node/{FAKE_MODULE}", json=body)

    assert resp.status == 500
    assert message in await resp.text()
    fake_log_node.make_logger.return_value.error.assert_called_once()


@pytest.mark.xfail(strict=True, reason="bug: `body` is unbound in the except handler when the node import fails, so the handler itself raises")
async def test_unknown_node_module_returns_error_message(fake_log_node, make_client):
    client = await make_client()

    resp = await client.post("/node/does_not_exist", json={"func": "ping"})

    assert resp.status == 500
    assert "does_not_exist" in await resp.text()


async def test_unknown_node_module_still_returns_500(fake_log_node, make_client):
    client = await make_client()

    resp = await client.post("/node/does_not_exist", json={"func": "ping"})

    assert resp.status == 500


# --- freedom.map fetch_status allow_set injection ---------------------------

@pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning")
async def test_map_fetch_status_admin_sees_everything(map_node, make_client):
    client = await make_client(auth_pool=FakeAuthPool([]))

    await client.post("/node/freedom.map", json={"func": "fetch_status"},
                      headers={"x-user-id": "u1", "x-user-role": "admin"})

    assert map_node.allow_sets == [None]


@pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning")
async def test_map_fetch_status_user_gets_allow_set_from_db(map_node, make_client):
    pool = FakeAuthPool([{"node": "robot.dummy", "node_id": "r1"}])
    client = await make_client(auth_pool=pool)

    resp = await client.post("/node/freedom.map", json={"func": "fetch_status"},
                             headers={"x-user-id": "u1", "x-user-role": "user"})

    assert resp.status == 200
    assert map_node.allow_sets == [{("robot.dummy", "r1")}]
    assert pool.queries[0][1] == ("u1",)


async def test_map_fetch_status_user_without_auth_pool_sees_nothing(map_node, make_client):
    client = await make_client()

    await client.post("/node/freedom.map", json={"func": "fetch_status"}, headers={"x-user-id": "u1"})

    assert map_node.allow_sets == [set()]


async def test_map_fetch_status_anonymous_is_not_filtered(map_node, make_client):
    client = await make_client()

    await client.post("/node/freedom.map", json={"func": "fetch_status"})

    assert map_node.allow_sets == ["unset"]


async def test_allow_set_only_injected_for_map_fetch_status(robots, make_client):
    client = await make_client()

    resp = await client.post(f"/node/{FAKE_MODULE}", json={"func": "ping"},
                             headers={"x-user-id": "u1", "x-user-role": "admin"})

    assert await resp.json() == "pong:r1"


# --- domain listing ----------------------------------------------------------

async def test_domain_view_lists_matching_domains(robots, make_client):
    client = await make_client()

    all_resp = await client.post(f"/domain/{FAKE_MODULE}")
    one_resp = await client.post(f"/domain/{FAKE_MODULE}", json={"id": "r2"})

    assert [d["id"] for d in await all_resp.json()] == ["r1", "r2"]
    assert await one_resp.json() == [{"id": "r2", "group": "robot"}]
