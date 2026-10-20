# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import zoneinfo
import datetime

from src import abstract, freedom
from src.repository import repository
from src.job.active import Domain, NodeDomain, Interface


class PostgreSQL(abstract.access.PostgreSQL[Domain], Interface):
    def __init__(self, domain:Domain):
        """Active job PostgreSQL connection
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
        columns = [f"{field.name} {self._convert_type(field.type)}" for field in dataclasses.fields(NodeDomain)]
        await self._pool.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._domain.schema}.{self._domain.table} (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at timestamptz NOT NULL DEFAULT NOW(),
                {', '.join(columns[2:])}
            );
        """)

    async def insert(self, name:str, task:dict, variables:list[dict]) -> dict:
        """Save an active job
        Args:
            name (str): Job name
            task (dict): Task contents
            variables (list[dict]): Task variables
        Returns:
            dict: Active job settings
        """
        time_zone = await self._pool.fetchval("show timezone")
        name_list = [field.name for field in dataclasses.fields(NodeDomain)]
        row = await self._pool.fetchrow(f"""
            INSERT INTO {self._domain.schema}.{self._domain.table} (name, task, variables)
            VALUES ($1, $2, $3)
            RETURNING {', '.join(name_list[:5])};
        """, name, task, variables)
        row = dict(row)
        row["created_at"] = row["created_at"].astimezone(zoneinfo.ZoneInfo(time_zone))
        return row

    async def fetch(self) -> list[dict]:
        """Get active jobs
        Returns:
            list[dict]: Active job settings
        """
        time_zone = await self._pool.fetchval("show timezone")
        tz = zoneinfo.ZoneInfo(time_zone)
        rows = await self._pool.fetch(f"""
            SELECT *
            FROM {self._domain.schema}.{self._domain.table}
        """)
        result = []
        for r in rows:
            d = dict(r)
            ca = d.get("created_at")
            if isinstance(ca, datetime.datetime) and ca.tzinfo is not None:
                d["created_at"] = ca.astimezone(tz)
            result.append(d)
        return result

    async def update(self, node_list:list[NodeDomain]):
        """Update an active job
        Args:
            node_list (list[NodeDomain]): List of active jobs
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(f"DELETE FROM {self._domain.schema}.{self._domain.table};")
                await conn.executemany(f"""
                    INSERT INTO {self._domain.schema}.{self._domain.table}
                    VALUES ({', '.join([f'${i+1}' for i in range(len(dataclasses.fields(NodeDomain)))])});
                """, [tuple(dataclasses.asdict(node).values()) for node in node_list])
