# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0
"""Integration tests for the user_interface HTTP API booted against config/dummy.py."""

import asyncio
import sys
import types

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from src import freedom
from src.freedom.middlewares.authz import authz_middleware
from src.freedom.user_interface import node as ui_node
from src.repository import repository

pytestmark = pytest.mark.asyncio(loop_scope="module")

EXPECTED_STRUCTURE = {
    "infrastructure": [
        "infrastructure.lamp",
        "infrastructure.shutter",
        "infrastructure.gate",
        "infrastructure.intersection",
    ],
    "equipment": ["equipment.database", "equipment.iotdatashare", "equipment.plc"],
    "robot": ["robot.dummy"],
    "job": ["job.active", "job.create"],
}

SEEDED_NODES = {
    "infrastructure.lamp": ["lamp_1", "lamp_2", "lamp_3"],
    "infrastructure.shutter": ["shutter_1"],
    "infrastructure.gate": ["gate_1"],
    "infrastructure.intersection": ["intersection_1"],
    "robot.dummy": ["robot_dummy_1", "robot_dummy_2", "robot_dummy_3"],
}

STATUS_KEYS = {"name", "state", "location", "info", "detail", "command", "node"}


class _CapturingRunner:
    """Stands in for web.AppRunner: records the app user_interface builds instead of serving it."""

    def __init__(self, app: web.Application):
        self.app = app
        _CapturingRunner.captured.set_result(app)

    async def setup(self):
        pass

    async def cleanup(self):
        pass


class _NoopSite:
    """Stands in for web.TCPSite so no real port (8080) is bound."""

    def __init__(self, *args, **kwargs):
        pass

    async def start(self):
        pass


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def app():
    """Boot the full dummy system via freedom.main.Node.init and capture the user_interface app."""
    _CapturingRunner.captured = asyncio.get_running_loop().create_future()
    fake_web = types.SimpleNamespace(
        Application=web.Application,
        view=web.view,
        AppRunner=_CapturingRunner,
        TCPSite=_NoopSite,
    )
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(ui_node, "web", fake_web)
        await freedom.main.Node.init("dummy")
        application = await asyncio.wait_for(_CapturingRunner.captured, timeout=10)
        yield application

    current = asyncio.current_task()
    tasks = [t for t in asyncio.all_tasks() if t is not current]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    repository.clear()
    sys.modules.pop("config.dummy", None)


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def client(app):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


async def post_node(client: TestClient, node: str, func: str, **body):
    resp = await client.post(f"/node/{node}", json={"func": func, **body})
    assert resp.status == 200, await resp.text()
    return await resp.json()


async def test_dummy_mode_skips_authz(app):
    assert authz_middleware not in app.middlewares
    assert len(app.middlewares) == 1  # cors_middleware only
    assert "auth_pool" not in app
    assert "casbin_authz" not in app


async def test_dummy_config_is_loaded(app):
    main = repository.retrieve(freedom.main.Node)[0]
    assert main.domain.interface == "Dummy"
    assert type(main._access).__name__ == "Dummy"


async def test_routes_registered(app):
    paths = {r.resource.canonical for r in app.router.routes() if r.resource is not None}
    assert {"/domain/{node}", "/node/{node}"} <= paths


async def test_fetch_structure(client):
    assert await post_node(client, "freedom.main", "fetch_structure") == EXPECTED_STRUCTURE


async def test_fetch_config_returns_seeded_robots(client):
    config = await post_node(client, "freedom.main", "fetch_config", kwargs={"node": "robot.dummy"})
    assert [d["name"] for d in config["node_domain"]] == SEEDED_NODES["robot.dummy"]


async def test_fetch_status_all(client):
    statuses = await post_node(client, "freedom.map", "fetch_status")
    for status in statuses:
        assert set(status) == STATUS_KEYS
        assert isinstance(status["state"], int)
        assert isinstance(status["info"], list)

    by_node: dict[str, list[str]] = {}
    for status in statuses:
        by_node.setdefault(status["node"], []).append(status["name"])
    assert by_node == SEEDED_NODES


async def test_fetch_status_robots_are_waiting(client):
    statuses = await post_node(client, "freedom.map", "fetch_status", kwargs={"node_name": "robot.dummy"})
    assert [s["name"] for s in statuses] == SEEDED_NODES["robot.dummy"]
    for status in statuses:
        assert status["node"] == "robot.dummy"
        assert status["state"] == 1  # State.WAITING (no active job)
        assert status["location"] is None


@pytest.mark.parametrize("node", list(SEEDED_NODES))
async def test_fetch_status_per_node(client, node):
    statuses = await post_node(client, "freedom.map", "fetch_status", kwargs={"node_name": node})
    assert [s["name"] for s in statuses] == SEEDED_NODES[node]
    assert {s["node"] for s in statuses} == {node}


async def test_fetch_status_admin_role_sees_everything(client):
    resp = await client.post(
        "/node/freedom.map",
        json={"func": "fetch_status"},
        headers={"x-user-id": "u1", "x-user-role": "admin"},
    )
    assert resp.status == 200
    names = {s["name"] for s in await resp.json()}
    assert names == {n for names in SEEDED_NODES.values() for n in names}


async def test_fetch_status_user_without_auth_pool_sees_nothing(client):
    # Dummy mode has no auth_pool, so a non-admin user gets an empty allow_set.
    resp = await client.post(
        "/node/freedom.map",
        json={"func": "fetch_status"},
        headers={"x-user-id": "u1", "x-user-role": "user"},
    )
    assert resp.status == 200
    assert await resp.json() == []


@pytest.mark.parametrize("node", list(SEEDED_NODES))
async def test_domain_retrieval(client, node):
    resp = await client.post(f"/domain/{node}")
    assert resp.status == 200, await resp.text()
    domains = await resp.json()
    assert [d["name"] for d in domains] == SEEDED_NODES[node]
    assert all(d["enable"] is True for d in domains)


async def test_domain_retrieval_filtered_by_name(client):
    resp = await client.post("/domain/robot.dummy", json={"name": "robot_dummy_2"})
    assert resp.status == 200
    domains = await resp.json()
    assert len(domains) == 1
    assert domains[0]["name"] == "robot_dummy_2"
    assert domains[0]["update_cycle"] == 1.0


async def test_domain_retrieval_infrastructure_uses_dummy_interface(client):
    resp = await client.post("/domain/infrastructure.lamp")
    assert {d["interface"] for d in await resp.json()} == {"Dummy"}


async def test_domain_retrieval_map_default_view(client):
    resp = await client.post("/domain/freedom.map")
    assert resp.status == 200
    [domain] = await resp.json()
    assert domain["default_view"] == {
        "center": [35.02345408903063, 137.13061702903593],
        "zoom": 15,
        "rotate": 0.0,
    }
    assert domain["image_list"] == []


async def test_domain_retrieval_no_match(client):
    resp = await client.post("/domain/robot.dummy", json={"name": "does_not_exist"})
    assert resp.status == 200
    assert await resp.json() == []


async def test_unknown_func_returns_500(client):
    resp = await client.post("/node/freedom.main", json={"func": "no_such_func"})
    assert resp.status == 500
    assert "no_such_func" in await resp.text()
