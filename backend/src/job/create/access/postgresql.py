# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import abstract, freedom
from src.job.create import Column, Domain, Interface
from src.repository import repository


class PostgreSQL(abstract.access.PostgreSQL[Domain], Interface):
    def __init__(self, domain:Domain):
        """ジョブ作成PostgreSQL接続
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
        columns = ', '.join(f"{field.name} {self._convert_type(field.type)}" for field in dataclasses.fields(Column))
        await self._pool.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._domain.schema}.{self._domain.table} (
                {columns},
                PRIMARY KEY (name)
            );
        """)

    async def fetch_name_list(self, user_id:str|None=None, is_admin:bool=False) -> list[str]:
        """ジョブ名リスト取得
        Args:
            user_id (str|None): ユーザID
            is_admin (bool): 管理者フラグ(Trueで全件取得)
        Returns:
            list[str]: ジョブ名リスト
        """
        if is_admin:
            rows = await self._pool.fetch(f"""
                SELECT name
                FROM {self._domain.schema}.{self._domain.table}
                ORDER BY name
            """)
            return [row["name"] for row in rows]
        if not user_id:
            return []
        rows = await self._pool.fetch(f"""
            SELECT jc.name
            FROM {self._domain.schema}.{self._domain.table} jc
            WHERE EXISTS (
                SELECT 1
                FROM authz.user_job_allow a
                WHERE a.user_id = $1
                  AND a.job_name = jc.name
            )
            ORDER BY jc.name
        """, user_id)
        return [row["name"] for row in rows]

    async def fetch_workspace(self, name:str) -> dict:
        """Blockly環境取得
        Args:
            name (str): ジョブ名
        Returns:
            dict: Blockly環境
        """
        return await self._pool.fetchval(f"""
            SELECT workspace
            FROM {self._domain.schema}.{self._domain.table}
            WHERE name = $1
        """, name)

    async def update(self, name:str, workspace:dict):
        """ジョブ更新
        Args:
            name (str): ジョブ名
            workspace (dict): Blockly環境
        """
        await self._pool.execute(f"""
            INSERT INTO {self._domain.schema}.{self._domain.table}
            VALUES ({', '.join([f'${i+1}' for i in range(len(dataclasses.fields(Column)))])})
            ON CONFLICT (name) DO UPDATE SET {', '.join([f'{field.name} = EXCLUDED.{field.name}' for field in dataclasses.fields(Column)])};
        """, name, workspace)

    async def delete(self, name:str):
        """ジョブ削除
        Args:
            name (str): ジョブ名
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(f"""
                    DELETE FROM {self._domain.schema}.{self._domain.table}
                    WHERE name = $1;
                """, name)
                await conn.execute("""
                    DELETE FROM authz.user_job_allow
                    WHERE job_name = $1;
                """, name)
