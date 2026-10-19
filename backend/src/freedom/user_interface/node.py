# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import sys

import asyncpg
from aiohttp import web
from aiohttp_middlewares import cors_middleware

from src import freedom
from src.freedom.authz.access.postgresql import (
    SQL_CREATE_AUTH_SCHEMA,
    SQL_CREATE_AUTHZ_SCHEMA,
    SQL_CREATE_CASBIN_RULE,
    SQL_CREATE_INDEXES,
    SQL_CREATE_USER_JOB_ALLOW,
    SQL_CREATE_USER_NODE_ALLOW,
    SQL_CREATE_USER_NODE_DENY,
    SQL_ENSURE_CONSTRAINTS,
)
from src.freedom.authz.casbin.seed import seed_policy_if_empty
from src.freedom.authz.enforcer import CasbinAuthz
from src.freedom.middlewares.authz import authz_middleware
from src.freedom.user_interface import Domain, logic
from src.repository import repository


class Node:
    def __init__(self, config:dict):
        """UIノード
        UIサーバとリクエストを管理する
        Args:
            config (dict): 設定リスト
        """
        # 設定変更時
        if old := repository.retrieve(self.__class__):
            self = old[0]
            self.domain = Domain(**config)
            self._logger.info(f"set domain: {self.domain}")
            return
        # 初回起動時
        self.domain = Domain(**config)
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__)
        self._task = asyncio.create_task(self._loop())
        self._logger.info(f"launch: self.domain={self.domain.__dict__}")
        repository.append(self)

    async def _loop(self):
        """処理ループ"""
        try:
            conf = repository.retrieve(freedom.main.Node)[0].domain.conf
            if getattr(conf.main, "interface", None) != "PostgreSQL":
                app = web.Application(middlewares=[cors_middleware(origins=self.domain.origin)])
            else:
                # PostgreSQL起動時のみCasbin防御を有効化
                app = web.Application(middlewares=[cors_middleware(origins=self.domain.origin), authz_middleware])
                auth_db_url = conf.main.dsn
                app["auth_pool"] = await asyncpg.create_pool(dsn=auth_db_url, min_size=1)
                async with app["auth_pool"].acquire() as conn:
                    async with conn.transaction():
                        # Better Auth用スキーマ（schemaのみ作成。テーブル群はBetter Auth migrateで作成）
                        await conn.execute(SQL_CREATE_AUTH_SCHEMA)
                        # authz スキーマ/テーブル/制約/インデックス/Casbin保存先
                        await conn.execute(SQL_CREATE_AUTHZ_SCHEMA)
                        await conn.execute(SQL_CREATE_USER_NODE_ALLOW)
                        await conn.execute(SQL_CREATE_USER_NODE_DENY)
                        await conn.execute(SQL_CREATE_USER_JOB_ALLOW)
                        await conn.execute(SQL_CREATE_CASBIN_RULE)
                        for q in SQL_CREATE_INDEXES:
                            await conn.execute(q)
                        await conn.execute(SQL_ENSURE_CONSTRAINTS)
                    # casbin_rule が空なら policy.seed.csv を投入
                    await seed_policy_if_empty(conn)
                # Casbin用URL変換
                authz_db_url = auth_db_url
                if authz_db_url.startswith("postgresql://"):
                    authz_db_url = "postgresql+asyncpg://" + authz_db_url[len("postgresql://"):]
                elif authz_db_url.startswith("postgres://"):
                    authz_db_url = "postgresql+asyncpg://" + authz_db_url[len("postgres://"):]
                casbin_authz = CasbinAuthz()
                await casbin_authz.init(authz_db_url)
                app["casbin_authz"] = casbin_authz
            app.add_routes([
                web.view('/domain/{node}', logic.Domain),
                web.view('/node/{node}', logic.Node),
            ])
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.domain.ip, self.domain.port)
            try:
                while sys.getrefcount(self) > 2:
                    try:
                        await site.start()
                        break
                    except Exception:
                        pass
                self._logger.info("start server")
                while sys.getrefcount(self) > 2:
                    await asyncio.sleep(0)
            finally:
                # Casbin有効時のみ閉じる
                if "auth_pool" in app:
                    try:
                        await app["auth_pool"].close()
                    except Exception:
                        pass
                await runner.cleanup()
                self._logger.info("close")
        except Exception as e:
            self._logger.exception(f"user_interface.Node._loop failed: {type(e)} {e}")
            raise
