# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import dataclasses
from datetime import datetime
import logging

from src import abstract
from src.repository import repository
from src.freedom.log import Domain, Column, Interface, access, logic


class Node(abstract.Node, abstract.Lifecycle):
    @staticmethod
    def _normalize_keywords(keywords:list[str]|None) -> list[str]|None:
        """キーワード正規化
        Args:
            keywords (list[str]|None): キーワード検索条件のリスト
        Returns:
            list[str]|None: 前後空白除去・空要素除外後のリスト
        """
        normalized = [item.strip() for item in (keywords or []) if isinstance(item, str) and item.strip()]
        return normalized or None

    @classmethod
    def configure(cls, config:dict=None) -> "Node":
        """ログノード構築・設定変更
        起動済みなら設定を反映し、未起動なら新規に起動する
        Args:
            config (dict): 設定 Noneで設定変更なし
        Returns:
            Node: ログノード
        """
        if old := repository.retrieve(cls):
            if config is not None:
                old[0].reconfigure(config)
            return old[0]
        return cls(config)

    def __init__(self, config:dict=None):
        """Freedomログノード
        システム内のログ情報を管理、保存する
        起動済みノードの設定変更はconfigure()またはreconfigure()を使う
        Args:
            config (dict): 設定
        """
        self.domain = Domain()
        self._log_list:list[Column] = list()
        self._access:Interface = None
        self._formatter = logging.Formatter("%(asctime)s.%(msecs)03d,%(name)s,%(levelname)s,%(message)s", '%Y-%m-%d,%H:%M:%S')
        self._stream_handler = logging.StreamHandler()
        self._stream_handler.setLevel(logging.DEBUG)
        self._stream_handler.setFormatter(self._formatter)
        self._output_handler = logic.Handler(self._log_list)
        self._output_handler.setLevel(logging.DEBUG)
        self._output_handler.setFormatter(self._formatter)
        self._logger = self.make_logger(__package__)
        self.start()
        self._logger.info(f"launch")
        repository.append(self)
        if config is not None:
            self.reconfigure(config)

    def reconfigure(self, config:dict):
        """設定変更
        Args:
            config (dict): 設定
        """
        domain = Domain(**config)
        new_access:Interface = getattr(access, domain.interface)(domain)
        old_access, self.domain, self._access = self._access, domain, new_access
        abstract.lifecycle.shutdown(old_access)
        self._logger.info(f"set domain: {self.domain}")

    async def _loop(self):
        """処理ループ
        停止時は残りのログを出力してから切断する
        """
        #TODO: ループ内でのエラー表示方法を考える
        temp_log_list:list[Column] = list()
        try:
            while self.running:
                try:
                    await asyncio.sleep(0)
                    await self._flush(temp_log_list)
                except asyncio.CancelledError:
                    break
                except Exception:
                    continue
        finally:
            try:
                await self._flush(temp_log_list)
            except Exception:
                pass
            await abstract.lifecycle.aclose(self._access)

    async def _flush(self, temp_log_list:list[Column]):
        """ログ出力
        Args:
            temp_log_list (list[Column]): 未出力ログ
        """
        temp_log_list.extend(self._log_list)
        self._log_list.clear()
        if self._access and temp_log_list:
            await self._access.insert(temp_log_list)
            temp_log_list.clear()

    def make_logger(self, name:str, prefix:str=None) -> logic.Adapter:
        """ロガー作成
        Args:
            name (str): ロガー名
            prefix (str): 接頭辞
        Returns:
            logic.Adapter: ロガー
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._stream_handler)
        logger.addHandler(self._output_handler)
        logger.propagate = False
        logger = logic.Adapter(logger, prefix)
        return logger

    async def fetch(self, begin_time:str, end_time:str, row_count:int|None=None, cursor_time:str|None=None, all_rows:bool=False, keywords:list[str]|None=None, levelnames:list[str]|None=None, sort_field:str="time", sort_direction:str="desc") -> list[dict]:
        """ログ取得
        Args:
            begin_time (str): 開始日時
            end_time (str): 終了日時
            row_count (int|None): 取得件数 Noneで全取得
            cursor_time (str|None): 追加取得時に基準にする時刻
            all_rows (bool): Trueで全件取得
            keywords (list[str]|None): キーワード検索条件のリスト
            levelnames (list[str]|None): ログレベル
            sort_field (str): ソート対象カラム
            sort_direction (str): ソート順 (asc/desc)
        Returns:
            list[dict]: ログ
        """
        effective_row_count = None if all_rows else (row_count if isinstance(row_count, int) else 100)
        effective_keywords = self._normalize_keywords(keywords)
        columns = await self._access.fetch(
            datetime.fromisoformat(begin_time),
            datetime.fromisoformat(end_time),
            effective_row_count,
            datetime.fromisoformat(cursor_time) if cursor_time else None,
            effective_keywords,
            levelnames,
            sort_field,
            sort_direction,
        )
        return [dataclasses.asdict(col) for col in columns]
