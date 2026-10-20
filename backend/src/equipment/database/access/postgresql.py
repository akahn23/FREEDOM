# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import asyncpg
from datetime import datetime
import json
import logging
from zoneinfo import ZoneInfo

from src import util
from src.equipment.database import NodeDomain


class PostgreSQL:
    """Database PostgreSQL connection
    Attributes:
        _domain (NodeDomain): Domain
        _pool (asyncpg.Pool|None): Connection pool
        _timezone (ZoneInfo|None): Time zone
        _task (asyncio.Task): Connection task
    """
    def __init__(self, domain:NodeDomain):
        """Instantiate
        Args:
            domain (NodeDomain): Domain
        """
        self._domain = domain
        self._pool:asyncpg.Pool|None = None
        self._timezone:ZoneInfo|None = None
        self._task = asyncio.create_task(self._connect())

    async def close(self):
        """Disconnect"""
        try:
            self._pool and await self._pool.close()
        except Exception:
            pass

    async def is_connected(self) -> bool:
        """Check the connection
        Returns:
            bool: Connection state
        """
        if not self._pool:
            return False
        try:
            await self._pool.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def upsert(self, keys:list[str], data:dict):
        """Insert or update
        Args:
            keys (list[str]): Match keys
            data (dict): Values to write
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
        """Connect"""
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
        """Initialization performed on connect
        Args:
            conn (asyncpg.Connection): Connection
        """
        await conn.set_type_codec("json", schema="pg_catalog", encoder=util.json.dumps, decoder=json.loads)
        await conn.set_type_codec("jsonb", schema="pg_catalog", encoder=util.json.dumps, decoder=json.loads)
        self._timezone = ZoneInfo(await conn.fetchval("SHOW TIMEZONE"))
