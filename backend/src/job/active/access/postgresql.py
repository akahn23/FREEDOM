# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import datetime
import zoneinfo

from src import abstract, freedom
from src.job.active import Domain, Interface, NodeDomain
from src.repository import repository


class PostgreSQL(abstract.access.PostgreSQL[Domain], Interface):
    def __init__(self, domain:Domain):
        """ジョブ実行PostgreSQL接続
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
        columns = [f"{field.name} {self._convert_type(field.type)}" for field in dataclasses.fields(NodeDomain)]
        await self._pool.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._domain.schema}.{self._domain.table} (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at timestamptz NOT NULL DEFAULT NOW(),
                {', '.join(columns[2:])}
            );
        """)

    async def insert(self, name:str, task:dict, variables:list[dict]) -> dict:
        """実行ジョブ保存
        Args:
            name (str): ジョブ名
            task (dict): タスク内容
            variables (list[dict]): タスク変数
        Returns:
            dict: 実行ジョブ設定
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
        """実行ジョブ取得
        Returns:
            list[dict]: 実行ジョブ設定
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
        """実行ジョブ更新
        Args:
            node_list (list[NodeDomain]): 実行ジョブリスト
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(f"DELETE FROM {self._domain.schema}.{self._domain.table};")
                await conn.executemany(f"""
                    INSERT INTO {self._domain.schema}.{self._domain.table}
                    VALUES ({', '.join([f'${i+1}' for i in range(len(dataclasses.fields(NodeDomain)))])});
                """, [tuple(dataclasses.asdict(node).values()) for node in node_list])
