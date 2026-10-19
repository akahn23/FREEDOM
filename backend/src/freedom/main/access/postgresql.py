# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import abstract, freedom
from src.freedom.main import Domain, Interface
from src.repository import repository


class PostgreSQL(abstract.access.PostgreSQL[Domain], Interface):
    def __init__(self, domain:Domain):
        """PostgreSQLログDB接続
        Args:
            domain (Domain): 設定
        """
        super().__init__(
            domain,
            repository.retrieve(freedom.log.Node)[0].make_logger(__name__)
        )

    async def _on_connect(self):
        """接続後イベント"""
        # テーブル作成
        await self._pool.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._domain.schema}.{self._domain.table} (
                node TEXT PRIMARY KEY,
                config JSONB
            );
        """)

    async def fetch(self, node:str) -> dict:
        """設定取得
        無ければNoneを返す
        Args:
            node (str): ノード名
        Returns:
            dict: 設定
        """
        row = await self._pool.fetchrow(
            f"SELECT config FROM {self._domain.schema}.{self._domain.table} WHERE node = $1;",
            node
        )
        return row['config'] if row else None

    async def update(self, node:str, config:dict):
        """設定更新
        Args:
            node (str): ノード名
            config (dict): 設定
        """
        await self._pool.execute(f"""
            INSERT INTO {self._domain.schema}.{self._domain.table}
            VALUES ($1, $2)
            ON CONFLICT (node) DO UPDATE SET config = EXCLUDED.config;
        """, node, config)
