# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import asyncio
import asyncpg
import dataclasses
from datetime import datetime, timedelta
import json
import logging

from src import abstract, util


class PostgreSQL[D:abstract.database.Domain](abstract.Lifecycle, abc.ABC):
    def __init__(self, domain:D, logger:logging.Logger):
        """PostgreSQL接続抽象クラス
        Args:
            domain (abstract.database.Domain): ドメイン
            logger (logging.Logger): ロガー
        """
        self._domain = domain
        self._logger = logger
        self._pool:asyncpg.Pool = None
        self.start()

    async def _loop(self):
        """接続確認ループ"""
        try:
            while self.running:
                if not await self._is_connect():
                    await self._connect()
                await asyncio.sleep(self._domain.update_cycle)
        finally:
            await self._close()

    async def _is_connect(self) -> bool:
        """接続判定"""
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
        """接続"""
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
        """接続時の初期化処理
        Args:
            conn (asyncpg.Connection): コネクタ
        """
        await conn.set_type_codec("json", schema="pg_catalog", encoder=util.json.dumps, decoder=json.loads)
        await conn.set_type_codec("jsonb", schema="pg_catalog", encoder=util.json.dumps, decoder=json.loads)

    async def _close(self):
        """切断"""
        if self._pool is None:
            return
        try:
            await self._pool.close()
        except Exception:
            pass
        self._pool = None

    def _convert_type(self, python_type:type) -> str:
        """PostgreSQL型変換
        Args:
            python_type (type): Python型
        Returns:
            str: PostgreSQL型
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
        """接続後イベント"""
        raise NotImplementedError("This method should be implemented by subclasses.")
