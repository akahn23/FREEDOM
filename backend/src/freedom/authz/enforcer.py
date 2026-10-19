# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
from importlib import resources
from typing import Optional

import casbin
import casbin_async_sqlalchemy_adapter
from casbin.model import Model

from src.freedom.authz.casbin_rule import CasbinRule


async def _maybe_await(v):
    if inspect.isawaitable(v):
        return await v
    return v


def _load_model_from_package() -> Model:
    m = Model()
    text = (resources.files("src.freedom.authz.casbin") / "model.conf").read_text(encoding="utf-8")
    m.load_model_from_text(text)
    return m


class CasbinAuthz:
    def __init__(self) -> None:
        self._enforcer: Optional[casbin.AsyncEnforcer] = None

    async def init(self, authz_db_url: str) -> None:
        # 起動時にschemaとtableを作成
        m = _load_model_from_package()
        adapter = casbin_async_sqlalchemy_adapter.Adapter(authz_db_url, db_class=CasbinRule)
        e = casbin.AsyncEnforcer(m, adapter)
        await _maybe_await(e.load_policy())
        try:
            await _maybe_await(e.build_role_links())
        except Exception:
            pass
        self._enforcer = e

    async def enforce(self, sub: str, obj: str, act: str) -> bool:
        if self._enforcer is None:
            raise RuntimeError("CasbinAuthz not initialized")
        return bool(await _maybe_await(self._enforcer.enforce(sub, obj, act)))
