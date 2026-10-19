# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Dict, Tuple

from aiohttp import web

from src.freedom.authz.classify import classify_action, make_object
from src.freedom.authz.enforcer import CasbinAuthz
from src.freedom.authz.repository import get_role_by_user_id


def _parse_target(path: str) -> Tuple[str, str]:
    """kindとnameの抽出"""
    if path.startswith("/node/"):
        return "node", path[len("/node/"):]
    if path.startswith("/domain/"):
        return "domain", path[len("/domain/"):]
    return "", ""


async def _read_json_body_cached(request: web.Request) -> Dict[str, Any]:
    if "cached_json" in request:
        return request["cached_json"]
    raw = (await request.text()).strip() or "{}"
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        body = {}
    request["cached_json"] = body
    return body


@web.middleware
async def authz_middleware(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
):
    kind, name = _parse_target(request.path)
    if kind not in ("node", "domain"):
        return await handler(request)
    authz: CasbinAuthz = request.app["casbin_authz"]
    auth_pool = request.app["auth_pool"]
    user_id = request.headers.get("x-user-id")
    role = "guest"
    if user_id:
        async with auth_pool.acquire() as conn:
            db_role = await get_role_by_user_id(conn, user_id)
        role = db_role or "guest"
    if kind == "node":
        body = await _read_json_body_cached(request)
        func = body.get("func", "")
        act = classify_action(name, func)
        obj = make_object("node", name)
    else:
        act = "read"
        obj = make_object("domain", name)
    allowed = await authz.enforce(role, obj, act)
    if not allowed:
        return web.json_response({"error": "forbidden", "reason": "casbin_deny"}, status=403)
    return await handler(request)
