# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import asyncpg

from src import util
from src.equipment.database import NodeDomain


class PostgreSQL:
    """データベース PostgreSQL接続
    Attributes:
        _domain (NodeDomain): ドメイン
        _pool (asyncpg.Pool|None): コネクションプール
        _timezone (ZoneInfo|None): タイムゾーン
        _task (asyncio.Task): 接続タスク
    """
    def __init__(self, domain:NodeDomain):
        """インスタンス化
        Args:
            domain (NodeDomain): ドメイン
        """
        self._domain = domain
        self._pool:asyncpg.Pool|None = None
        self._timezone:ZoneInfo|None = None
        self._task = asyncio.create_task(self._connect())

    async def close(self):
        """切断"""
        try:
            self._pool and await self._pool.close()
        except Exception:
            pass

    async def is_connected(self) -> bool:
        """接続確認
        Returns:
            bool: 接続状態
        """
        if not self._pool:
            return False
        try:
            await self._pool.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def upsert(self, keys:list[str], data:dict):
        """追加・更新
        Args:
            keys (list[str]): 一致キー
            data (dict): 書込み値
        """
        for k, v in data.items():
            if isinstance(v, datetime) and v.tzinfo is None:
                data[k] = v.astimezone(self._timezone)
        sql = f"""
            INSERT INTO {self._domain.schema}.{self._domain.table} ({', '.join(data.keys())})
            VALUES ({', '.join(['$' + str(i + 1) for i in range(len(data))])})
        """
        if keys:
            sql += f"""
                ON CONFLICT ({', '.join(keys)}) DO UPDATE SET {', '.join([f'{k} = EXCLUDED.{k}' for k in data.keys() if k not in keys])}
            """
        return await self._pool.execute(sql, *data.values())

    async def _connect(self):
        """接続"""
        while self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    dsn=self._domain.dsn,
                    timeout=self._domain.timeout,
                    command_timeout=self._domain.timeout,
                    init=self._init_connection,
                    min_size=1
                )
            except Exception:
                await asyncio.sleep(0)

    async def _init_connection(self, conn:asyncpg.Connection):
        """接続時の初期化処理
        Args:
            conn (asyncpg.Connection): コネクタ
        """
        await conn.set_type_codec("json", schema="pg_catalog", encoder=util.json.dumps, decoder=json.loads)
        await conn.set_type_codec("jsonb", schema="pg_catalog", encoder=util.json.dumps, decoder=json.loads)
        self._timezone = ZoneInfo(await conn.fetchval("SHOW TIMEZONE"))
