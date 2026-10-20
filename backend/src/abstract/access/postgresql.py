# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import asyncio
import asyncpg
import dataclasses
from datetime import datetime, timedelta
import json
import logging
import sys

from src import abstract, util


class PostgreSQL[D:abstract.database.Domain](abc.ABC):
    def __init__(self, domain:D, logger:logging.Logger):
        """Abstract PostgreSQL connection class
        Args:
            domain (abstract.database.Domain): Domain
            logger (logging.Logger): Logger
        """
        self._domain = domain
        self._logger = logger
        self._pool:asyncpg.Pool = None
        self._task = asyncio.create_task(self._loop())

    async def _loop(self):
        """Connection check loop"""
        try:
            while sys.getrefcount(self) > 2:
                if not await self._is_connect():
                    await self._connect()
                await asyncio.sleep(self._domain.update_cycle)
        finally:
            await self._close()

    async def _is_connect(self) -> bool:
        """Whether connected"""
        if not self._pool:
            return False
        try:
            await self._pool.execute("SELECT 1")
            return True
        except Exception as e:
            self._logger.error(f"disconnect: {type(e)} {e}")
            await self._close()
            return False

    async def _connect(self):
        """Connect"""
        try:
            self._pool = await asyncpg.create_pool(dsn=self._domain.dsn, init=self._init_connection, min_size=1)
            self._logger.info(f"connect: {self._domain.dsn}")
        except Exception:
            return
        try:
            await self._pool.execute(f"CREATE SCHEMA IF NOT EXISTS {self._domain.schema};")
            await self._on_connect()
        except Exception as e:
            self._logger.error(f"Failed to on_connect: {type(e)} {e}")
            await self._close()

    async def _init_connection(self, conn:asyncpg.Connection):
        """Initialization performed on connect
        Args:
            conn (asyncpg.Connection): Connection
        """
        await conn.set_type_codec("json", schema="pg_catalog", encoder=util.json.dumps, decoder=json.loads)
        await conn.set_type_codec("jsonb", schema="pg_catalog", encoder=util.json.dumps, decoder=json.loads)

    async def _close(self):
        """Disconnect"""
        if self._pool is None:
            return
        try:
            await self._pool.close()
        except Exception:
            pass
        self._pool = None

    def _convert_type(self, python_type:type) -> str:
        """PostgreSQL type conversion
        Args:
            python_type (type): Python type
        Returns:
            str: PostgreSQL type
        """
        type_mapping = {
            int: 'integer',
            float: 'double precision',
            str: 'text',
            bool: 'boolean',
            bytes: 'bytea',
            type(None): 'null',
            datetime: 'timestamptz',
            datetime.date: 'date',
            datetime.time: 'time',
            timedelta: 'interval',
        }
        if python_type in type_mapping.keys():
            return type_mapping[python_type]
        if dataclasses.is_dataclass(python_type):
            return 'jsonb'
        if hasattr(python_type, '__iter__'):
            return 'jsonb'
        return 'text'

    @abc.abstractmethod
    async def _on_connect(self):
        """Post-connection event"""
        raise NotImplementedError("This method should be implemented by subclasses.")
