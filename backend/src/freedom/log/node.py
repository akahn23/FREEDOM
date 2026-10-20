# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import dataclasses
from datetime import datetime
import logging
import sys

from src import abstract
from src.repository import repository
from src.freedom.log import Domain, Column, Interface, access, logic


class Node(abstract.Node):
    RETRY_BASE_DELAY:float = 0.5
    RETRY_MAX_DELAY:float = 30.0
    MAX_CONSECUTIVE_FAILURES:int = 10
    MAX_BUFFERED_LOGS:int = 100_000
    SHUTDOWN_FLUSH_TIMEOUT:float = 5.0

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

    def __init__(self, config:dict=None):
        """Freedomログノード
        システム内のログ情報を管理、保存する
        Args:
            config (dict): 設定
        """
        # 設定変更時
        if old := repository.retrieve(self.__class__):
            self = old[0]
            self.domain = Domain(**config)
            self._access = getattr(access, self.domain.interface)(self.domain)
            self._logger.info(f"set domain: {self.domain}")
            return
        # 初回起動時
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
        # 書込みエラー通知用 (DB出力ハンドラを経由させずエラーの再帰を防ぐ)
        self._writer_logger = logging.getLogger(f"{__package__}.writer")
        self._writer_logger.setLevel(logging.DEBUG)
        self._writer_logger.addHandler(self._stream_handler)
        self._writer_logger.propagate = False
        self._task = asyncio.create_task(self._loop())
        self._logger = self.make_logger(__package__)
        self._logger.info(f"launch")
        repository.append(self)

    async def _loop(self):
        """処理ループ
        書込み失敗時は指数バックオフで再試行し、連続失敗が上限に達したバッチは
        トレースバック付きでエラー出力して破棄する
        ループ終了時(キャンセル含む)はバッファ済みのログを書き出す
        """
        batch:list[Column] = list()
        failures = 0
        try:
            while sys.getrefcount(self) > 2:
                await asyncio.sleep(0)
                self._trim_buffer()
                if not batch:
                    batch.extend(self._log_list)
                    self._log_list.clear()
                if not (self._access and batch):
                    continue
                try:
                    await self._access.insert(batch)
                except Exception:
                    failures += 1
                    if failures >= self.MAX_CONSECUTIVE_FAILURES:
                        self._writer_logger.error(f"log write failed {failures} times in a row, dropping {len(batch)} logs", exc_info=True)
                        batch.clear()
                        failures = 0
                        continue
                    delay = self._backoff_delay(failures)
                    self._writer_logger.warning(f"log write failed ({failures}/{self.MAX_CONSECUTIVE_FAILURES}), retry in {delay:.2f}s", exc_info=failures == 1)
                    await asyncio.sleep(delay)
                    continue
                if failures:
                    self._writer_logger.info(f"log write recovered after {failures} failures")
                failures = 0
                batch.clear()
        finally:
            await self._flush(batch)

    def _backoff_delay(self, failures:int) -> float:
        """再試行待機時間
        Args:
            failures (int): 連続失敗回数
        Returns:
            float: 待機時間[s]
        """
        return min(self.RETRY_BASE_DELAY * 2 ** (failures - 1), self.RETRY_MAX_DELAY)

    def _trim_buffer(self):
        """未書込みログの上限超過分を古い順に破棄"""
        overflow = len(self._log_list) - self.MAX_BUFFERED_LOGS
        if overflow > 0:
            del self._log_list[:overflow]
            self._writer_logger.error(f"log buffer full ({self.MAX_BUFFERED_LOGS}), dropped {overflow} oldest logs")

    async def _flush(self, batch:list[Column]):
        """終了時の書き出し
        Args:
            batch (list[Column]): 書込み中のバッチ
        """
        batch.extend(self._log_list)
        self._log_list.clear()
        if not batch:
            return
        if not self._access:
            self._writer_logger.error(f"shutdown: no log storage configured, {len(batch)} logs not written")
            return
        try:
            async with asyncio.timeout(self.SHUTDOWN_FLUSH_TIMEOUT):
                await self._access.insert(batch)
            batch.clear()
        except Exception:
            self._writer_logger.error(f"shutdown: failed to flush {len(batch)} logs", exc_info=True)

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
