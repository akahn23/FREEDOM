# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import abstract, freedom
from src.repository import repository
from src.freedom.main import Domain, Interface


class PostgreSQL(abstract.access.PostgreSQL[Domain], Interface):
    def __init__(self, domain:Domain):
        """PostgreSQL log database connection
        Args:
            domain (Domain): Settings
        """
        super().__init__(
            domain,
            repository.retrieve(freedom.log.Node)[0].make_logger(__name__)
        )

    async def _on_connect(self):
        """Post-connection event"""
        # テーブル作成
        await self._pool.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._domain.schema}.{self._domain.table} (
                node TEXT PRIMARY KEY,
                config JSONB
            );
        """)

    async def fetch(self, node:str) -> dict:
        """Get the settings
        Return None if not found
        Args:
            node (str): Node name
        Returns:
            dict: Settings
        """
        row = await self._pool.fetchrow(
            f"SELECT config FROM {self._domain.schema}.{self._domain.table} WHERE node = $1;",
            node
        )
        return row['config'] if row else None

    async def update(self, node:str, config:dict):
        """Update the settings
        Args:
            node (str): Node name
            config (dict): Settings
        """
        await self._pool.execute(f"""
            INSERT INTO {self._domain.schema}.{self._domain.table}
            VALUES ($1, $2)
            ON CONFLICT (node) DO UPDATE SET config = EXCLUDED.config;
        """, node, config)
