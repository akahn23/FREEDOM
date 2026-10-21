"""Smoke tests for the user_interface HTTP API booted from config.dummy.

The real aiohttp application is built inside ``user_interface.Node._loop`` and
bound to localhost:8080. The ``web`` module used by that file is replaced with
a namespace whose ``AppRunner`` captures the app and whose ``TCPSite`` is a
no-op, so the captured app can be served by ``aiohttp.test_utils.TestServer``
on a random port. No PostgreSQL is needed: config.dummy uses Dummy access
classes throughout.

The API only exposes two POST views: ``/domain/{node}`` (list node domains)
and ``/node/{node}`` (call a node method by name). There are no GET routes.
"""

import asyncio
import logging
import sys
import types
from typing import ClassVar

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from src import freedom
from src.freedom.user_interface import node as ui_node
from src.repository import repository

BOOT_TIMEOUT = 10.0
ORIGIN = "http://localhost:3000"


class _CapturingAppRunner:
    apps: ClassVar[list[web.Application]] = []

    def __init__(self, app, *args, **kwargs):
        self.app = app
        _CapturingAppRunner.apps.append(app)

    async def setup(self):
        pass

    async def cleanup(self):
        pass


class _NoopTCPSite:
    def __init__(self, runner, host=None, port=None, *args, **kwargs):
        self.runner = runner
        self.host = host
        self.port = port

    async def start(self):
        pass

    async def stop(self):
        pass


def _fake_web():
    return types.SimpleNamespace(
        Application=web.Application,
        view=web.view,
        Request=web.Request,
        Response=web.Response,
        json_response=web.json_response,
        AppRunner=_CapturingAppRunner,
        TCPSite=_NoopTCPSite,
    )


async def _boot():
    await freedom.main.Node.init("dummy")
    loop = asyncio.get_running_loop()
    deadline = loop.time() + BOOT_TIMEOUT
    while not _CapturingAppRunner.apps:
        if loop.time() > deadline:
            raise TimeoutError("user_interface app was never built")
        await asyncio.sleep(0)
    client = TestClient(TestServer(_CapturingAppRunner.apps[-1]))
    await client.start_server()
    return client


async def _shutdown(client):
    if client is not None:
        await client.close()
    current = asyncio.current_task()
    tasks = [t for t in asyncio.all_tasks() if t is not current]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


def _strip_log_handlers():
    log_nodes = repository.retrieve(freedom.log.Node)
    if not log_nodes:
        return
    handlers = {log_nodes[0]._stream_handler, log_nodes[0]._output_handler}
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            for handler in list(logger.handlers):
                if handler in handlers:
                    logger.removeHandler(handler)


@pytest.fixture(scope="module")
def api():
    """Yield ``(runner, client)``; run requests with ``runner.run(...)``."""
    mp = pytest.MonkeyPatch()
    mp.setattr(ui_node, "web", _fake_web())
    _CapturingAppRunner.apps.clear()
    runner = asyncio.Runner()
    client = None
    try:
        client = runner.run(_boot())
        yield runner, client
    finally:
        try:
            runner.run(_shutdown(client))
        finally:
            runner.close()
            _strip_log_handlers()
            repository.clear()
            sys.modules.pop("config.dummy", None)
            _CapturingAppRunner.apps.clear()
            mp.undo()


def _request(api, method, path, **kwargs):
    runner, client = api

    async def go():
        resp = await client.request(method, path, **kwargs)
        body = await resp.read()
        return resp, body

    return runner.run(go())


def _post_json(api, path, payload=None):
    runner, client = api

    async def go():
        resp = await client.post(path, json=payload)
        if resp.content_type == "application/json":
            body = await resp.json()
        else:
            body = await resp.text()
        return resp.status, body

    return runner.run(go())


def _call(api, node, func, kwargs=None, domain=None):
    payload = {"func": func}
    if kwargs is not None:
        payload["kwargs"] = kwargs
    if domain is not None:
        payload["domain"] = domain
    return _post_json(api, f"/node/{node}", payload)


EXPECTED_STATUS = {
    ("infrastructure.lamp", "lamp_1"),
    ("infrastructure.lamp", "lamp_2"),
    ("infrastructure.lamp", "lamp_3"),
    ("infrastructure.shutter", "shutter_1"),
    ("infrastructure.gate", "gate_1"),
    ("infrastructure.intersection", "intersection_1"),
    ("robot.dummy", "robot_dummy_1"),
    ("robot.dummy", "robot_dummy_2"),
    ("robot.dummy", "robot_dummy_3"),
}


def test_app_routes_are_the_two_post_views(api):
    _, client = api
    routes = {
        (r.method, r.resource.canonical)
        for r in client.server.app.router.routes()
    }
    assert ("*", "/domain/{node}") in routes
    assert ("*", "/node/{node}") in routes
    assert len(routes) == 2


def test_map_fetch_status_lists_dummy_nodes(api):
    status, body = _call(api, "freedom.map", "fetch_status")
    assert status == 200
    assert isinstance(body, list)
    assert {(s["node"], s["name"]) for s in body} == EXPECTED_STATUS
    for s in body:
        assert set(s) == {"name", "state", "location", "info", "detail", "command", "node"}
        assert isinstance(s["state"], int)
        assert -1 <= s["state"] <= 5
        assert isinstance(s["info"], list)
        assert isinstance(s["detail"], list)
        assert isinstance(s["command"], list)


def test_map_fetch_status_filtered_by_node_name(api):
    status, body = _call(api, "freedom.map", "fetch_status", {"node_name": "infrastructure.lamp"})
    assert status == 200
    assert sorted(s["name"] for s in body) == ["lamp_1", "lamp_2", "lamp_3"]
    assert {s["node"] for s in body} == {"infrastructure.lamp"}


def test_map_fetch_status_admin_header_is_unfiltered(api):
    runner, client = api

    async def go():
        resp = await client.post(
            "/node/freedom.map",
            json={"func": "fetch_status"},
            headers={"x-user-id": "u1", "x-user-role": "admin"},
        )
        return resp.status, await resp.json()

    status, body = runner.run(go())
    assert status == 200
    assert len(body) == len(EXPECTED_STATUS)


def test_map_fetch_status_non_admin_without_auth_pool_sees_nothing(api):
    runner, client = api

    async def go():
        resp = await client.post(
            "/node/freedom.map",
            json={"func": "fetch_status"},
            headers={"x-user-id": "u1", "x-user-role": "user"},
        )
        return resp.status, await resp.json()

    assert runner.run(go()) == (200, [])


def test_main_fetch_structure(api):
    status, body = _call(api, "freedom.main", "fetch_structure")
    assert status == 200
    assert body == {
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


def test_main_fetch_form(api):
    status, body = _call(api, "freedom.main", "fetch_form", {"node": "freedom.user_interface"})
    assert status == 200
    assert set(body) == {"sub_title", "update_cycle"}
    assert body["update_cycle"]["type"] == "number"


def test_main_fetch_config_for_map(api):
    status, body = _call(api, "freedom.main", "fetch_config", {"node": "freedom.map"})
    assert status == 200
    assert body["default_view"]["center"] == [35.02345408903063, 137.13061702903593]
    assert body["default_view"]["zoom"] == 15
    assert body["image_list"] == []


def test_log_fetch_returns_rows(api):
    status, body = _call(
        api,
        "freedom.log",
        "fetch",
        {
            "begin_time": "2000-01-01T00:00:00+00:00",
            "end_time": "2100-01-01T00:00:00+00:00",
            "row_count": 5,
        },
    )
    assert status == 200
    assert isinstance(body, list)
    assert 0 < len(body) <= 5
    for row in body:
        assert set(row) == {"time", "name", "levelname", "message"}


def test_domain_map(api):
    status, body = _post_json(api, "/domain/freedom.map")
    assert status == 200
    assert isinstance(body, list) and len(body) == 1
    assert body[0]["default_view"]["zoom"] == 15


def test_domain_lamp_lists_all_and_filters(api):
    status, body = _post_json(api, "/domain/infrastructure.lamp")
    assert status == 200
    assert sorted(d["name"] for d in body) == ["lamp_1", "lamp_2", "lamp_3"]

    status, body = _post_json(api, "/domain/infrastructure.lamp", {"name": "lamp_2"})
    assert status == 200
    assert [d["name"] for d in body] == ["lamp_2"]


def test_node_call_with_domain_selector(api):
    status, body = _call(api, "infrastructure.gate", "fetch_status", domain={"name": "gate_1"})
    assert status == 200
    assert body["name"] == "gate_1"
    assert isinstance(body["state"], int)


def test_unknown_route_is_404(api):
    resp, _ = _request(api, "GET", "/no/such/route")
    assert resp.status == 404
    resp, _ = _request(api, "POST", "/node")
    assert resp.status == 404


def test_get_on_post_only_view_is_405(api):
    resp, _ = _request(api, "GET", "/node/freedom.map")
    assert resp.status == 405
    resp, _ = _request(api, "GET", "/domain/freedom.map")
    assert resp.status == 405


def test_missing_func_is_500_with_message(api):
    status, body = _post_json(api, "/node/freedom.map", {"kwargs": {}})
    assert status == 500
    assert body == "'func'"


def test_unknown_method_is_500(api):
    status, body = _call(api, "freedom.map", "no_such_method")
    assert status == 500
    assert "no_such_method" in body


def test_unknown_node_module_is_500(api):
    status, _ = _call(api, "freedom.no_such_node", "fetch_status")
    assert status == 500


@pytest.mark.xfail(
    strict=True,
    reason=(
        "logic.Node.post references `body` in its except block before it is "
        "assigned, so an unknown node module raises UnboundLocalError and "
        "aiohttp returns its generic 500 page instead of str(e)"
    ),
)
def test_unknown_node_module_error_message(api):
    _, body = _call(api, "freedom.no_such_node", "fetch_status")
    assert "no_such_node" in body


def test_cors_allows_configured_origin(api):
    resp, _ = _request(
        api,
        "POST",
        "/node/freedom.main",
        json={"func": "fetch_structure"},
        headers={"Origin": ORIGIN},
    )
    assert resp.status == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == ORIGIN
