# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import zoneinfo
from datetime import datetime, timedelta

from src import abstract, freedom
from src.freedom.log import Column, Domain, Interface
from src.repository import repository


class PostgreSQL(abstract.access.PostgreSQL[Domain], Interface):
    @staticmethod
    def _build_keyword_conditions(keywords:list[str], start_index:int) -> tuple[list[str], list[str], int]:
        """キーワード検索条件のWHERE断片生成
        Args:
            keywords (list[str]): キーワード検索条件のリスト
            start_index (int): 使用開始するプレースホルダ番号
        Returns:
            tuple[list[str], list[str], int]:
                (conditions, params, next_param_index)
                conditions: OR結合するキーワード条件の断片リスト
                params: プレースホルダに対応するパラメータ
                next_param_index: 次に使う$Nの番号
        """
        conditions: list[str] = []
        params: list[str] = []
        i = start_index
        for item in keywords:
            terms = [term for term in str(item).split() if term]
            if not terms:
                continue
            term_conditions: list[str] = []
            for term in terms:
                term_conditions.append(
                    f"(CAST(time AS TEXT) ILIKE ${i}"
                    f" OR name ILIKE ${i}"
                    f" OR levelname ILIKE ${i}"
                    f" OR message ILIKE ${i})"
                )
                params.append(f"%{term}%")
                i += 1
            conditions.append(f"({' AND '.join(term_conditions)})")
        return conditions, params, i

    def __init__(self, domain:Domain):
        """PostgreSQLログDB接続
        Args:
            domain (Domain): 設定
        """
        super().__init__(
            domain,
            repository.retrieve(freedom.log.Node)[0].make_logger(__name__)
        )
        self._last_time:datetime = None

    async def _on_connect(self):
        """接続後イベント"""
        # テーブル作成
        columns = ', '.join(f"{field.name} {self._convert_type(field.type)}" for field in dataclasses.fields(Column))
        await self._pool.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._domain.schema}.{self._domain.table} (
                {columns},
                PRIMARY KEY (time)
            ) PARTITION BY RANGE (time);
        """)
        # 終端日時取得
        last_time:datetime = await self._pool.fetchval(f"""
            SELECT time
            FROM {self._domain.schema}.{self._domain.table}
            ORDER BY time DESC
            LIMIT 1;
        """)
        if last_time is None:
            self._last_time = datetime.min
        else:
            time_zone = await self._pool.fetchval("show timezone")
            self._last_time = last_time.astimezone(zoneinfo.ZoneInfo(time_zone))

    async def _create_partition(self, time:datetime):
        """パーティション作成
        Args:
            time (datetime): 作成日時
        """
        time_zone = await self._pool.fetchval("show timezone")
        time = time.replace(tzinfo=zoneinfo.ZoneInfo(time_zone))
        partition_name = f"{self._domain.table}_{time.strftime('%Y_%m_%d')}"
        await self._pool.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._domain.schema}.{partition_name} PARTITION OF {self._domain.schema}.{self._domain.table}
            FOR VALUES FROM ('{time.strftime("%Y-%m-%d 00:00:00%z")}') TO ('{(time+timedelta(days=1)).strftime("%Y-%m-%d 00:00:00%z")}');
        """)
        self._logger.info(f"create partition: {partition_name}")

    async def _delete_partition(self):
        """パーティション削除"""
        partitions = await self._pool.fetch(f"""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = '{self._domain.schema}' AND tablename LIKE '{self._domain.table}_%'
            ORDER BY tablename ASC;
        """)
        for partition in partitions[:-self._domain.retention_period]:
            await self._pool.execute(f"DROP TABLE IF EXISTS {self._domain.schema}.{partition['tablename']} CASCADE;")
            self._logger.info(f"delete partition: {partition['tablename']}")

    async def insert(self, log_list:list[Column]):
        """ログ挿入
        パーティション整理も行う
        Args:
            log_list (list[Column]): ログリスト
        """
        for log in log_list:
            if log.time.date() > self._last_time.date():
                await self._create_partition(log.time)
                await self._delete_partition()
                self._last_time = log.time
        query = f"""
            INSERT INTO {self._domain.schema}.{self._domain.table}
            VALUES ({', '.join([f'${i+1}' for i in range(len(dataclasses.fields(Column)))])});
        """
        await self._pool.executemany(query, [dataclasses.astuple(log) for log in log_list])

    @staticmethod
    def _build_fetch_conditions(begin_time:datetime, end_time:datetime, cursor_time:datetime|None, sort_direction_safe:str, levelnames:list[str]|None, keywords:list[str]|None) -> tuple[list[str], list, int]:
        """パラメータ化クエリ
        Args:
            begin_time (datetime): 開始日時
            end_time (datetime): 終了日時
            cursor_time (datetime|None): カーソル時刻
            sort_direction_safe (str): "ASC" または "DESC"
            levelnames (list[str]|None): ログレベル
            keywords (list[str]|None): キーワード検索条件のリスト
        Returns:
            tuple[list[str], list, int]:
                (conditions, params, next_param_index)
                conditions: WHERE句にANDで結合する断片のリスト
                params: パラメータのリスト
                next_param_index: 次に使う$Nの番号
        """
        conditions: list[str] = ["time BETWEEN $1 AND $2"]
        params: list = [begin_time, end_time]
        i = 3
        if cursor_time is not None:
            cursor_op = ">" if sort_direction_safe == "ASC" else "<"
            conditions.append(f"time {cursor_op} ${i}")
            params.append(cursor_time)
            i += 1
        if levelnames:
            conditions.append(f"levelname = ANY(${i})")
            params.append(levelnames)
            i += 1
        if keywords:
            keyword_groups, keyword_params, i = PostgreSQL._build_keyword_conditions(keywords, i)
            params.extend(keyword_params)
            if keyword_groups:
                conditions.append(f"({' OR '.join(keyword_groups)})")
        return conditions, params, i

    async def fetch(self, begin_time:datetime, end_time:datetime, row_count:int|None=None, cursor_time:datetime|None=None, keywords:list[str]|None=None, levelnames:list[str]|None=None, sort_field:str="time", sort_direction:str="desc") -> list[Column]:
        """ログ取得
        Args:
            begin_time (datetime): 開始日時
            end_time (datetime): 終了日時
            row_count (int|None): 取得件数 Noneで全取得
            cursor_time (datetime|None): 追加取得時に基準にする時刻
            keywords (list[str]|None): キーワード検索条件のリスト
            levelnames (list[str]|None): ログレベル
            sort_field (str): ソート対象カラム
            sort_direction (str): ソート順 (asc/desc)
        Returns:
            list[Column]: ログ
        """
        if row_count == "null":
            row_count = None
        allowed_fields = {field.name for field in dataclasses.fields(Column)}
        sort_field_safe = sort_field if sort_field in allowed_fields else "time"
        sort_direction_safe = "ASC" if str(sort_direction).lower() == "asc" else "DESC"
        conditions, params, param_index = self._build_fetch_conditions(
            begin_time, end_time,
            cursor_time, sort_direction_safe,
            levelnames, keywords,
        )
        select_cols = ', '.join(field.name for field in dataclasses.fields(Column))
        base_query = f"""
            SELECT {select_cols}
            FROM {self._domain.schema}.{self._domain.table}
            WHERE {' AND '.join(conditions)}
            ORDER BY {sort_field_safe} {sort_direction_safe}
        """
        if row_count is not None:
            query = base_query + f"\nLIMIT ${param_index};"
            params.append(row_count)
        else:
            query = base_query + ";"
        rows = await self._pool.fetch(query, *params)
        tzinfo = zoneinfo.ZoneInfo("UTC")
        return [
            Column(**{**row, "time": row["time"].astimezone(tzinfo)})
            for row in rows
        ]
