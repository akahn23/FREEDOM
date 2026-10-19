# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import zoneinfo
from datetime import datetime

from src.freedom.log import Column, Domain, Interface

UTC = zoneinfo.ZoneInfo("UTC")


class Dummy(Interface):
    @staticmethod
    def _keyword_match(values:list[str], keyword_item:str) -> bool:
        """キーワード条件を満たすか判定
        Args:
            values (list[str]): 検索対象の値リスト
            keyword_item (str): OR条件1項目（空白区切りでAND）
        Returns:
            bool: 条件を満たす場合はTrue
        """
        terms = [term.lower() for term in str(keyword_item).split() if term]
        if not terms:
            return False
        normalized_values = [value.lower() for value in values]
        return all(any(term in value for value in normalized_values) for term in terms)

    def _to_utc(self, dt:datetime) -> datetime:
        """日時をUTCへ正規化
        Args:
            dt (datetime): 変換元日時
        Returns:
            datetime: UTC日時
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self._source_tz).astimezone(UTC)
        return dt.astimezone(UTC)

    def __init__(self, domain:Domain):
        """ダミーログDB接続
        Args:
            domain (Domain): 設定
        """
        self._retention_period = domain.retention_period
        self._log_list:list[Column] = list()
        if hasattr(domain, "timezone") and domain.timezone:
            self._source_tz = zoneinfo.ZoneInfo(domain.timezone)
        else:
            self._source_tz = datetime.now().astimezone().tzinfo

    async def insert(self, log_list:list[Column]):
        """ログ挿入
        Args:
            log_list (list[Column]): ログリスト
        """
        self._log_list.extend(log_list)
        for i, log in enumerate(self._log_list):
            if (log_list[-1].time.date()-log.time.date()).days <= self._retention_period:
                self._log_list = self._log_list[i:]
                return

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
        begin_utc = self._to_utc(begin_time)
        end_utc = self._to_utc(end_time)
        cursor_utc = None
        if cursor_time is not None:
            cursor_utc = self._to_utc(cursor_time)
        sort_field_safe = sort_field if sort_field in {"time", "name", "levelname", "message"} else "time"
        sort_desc = str(sort_direction).lower() != "asc"
        def sort_key(log: Column):
            if sort_field_safe == "time":
                return self._to_utc(log.time)
            return str(getattr(log, sort_field_safe, ""))
        sorted_logs = sorted(self._log_list, key=sort_key, reverse=sort_desc)
        ret:list[Column] = list()
        limit = row_count if isinstance(row_count, int) else None
        for log in sorted_logs:
            log_dt_utc = self._to_utc(log.time)
            if begin_utc <= log_dt_utc <= end_utc:
                if cursor_utc is not None:
                    if sort_desc and not (log_dt_utc < cursor_utc):
                        continue
                    if not sort_desc and not (log_dt_utc > cursor_utc):
                        continue
                if levelnames and log.levelname not in levelnames:
                    continue
                if keywords:
                    values = [str(log_dt_utc), str(log.name), str(log.levelname), str(log.message)]
                    if not any(self._keyword_match(values, item) for item in keywords):
                        continue
                ret.append(dataclasses.replace(log, time=log_dt_utc))
                if limit is not None and len(ret) >= limit:
                    break
        return ret
