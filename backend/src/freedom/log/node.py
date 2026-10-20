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
    @staticmethod
    def _normalize_keywords(keywords:list[str]|None) -> list[str]|None:
        """Normalize keywords
        Args:
            keywords (list[str]|None): List of keyword search conditions
        Returns:
            list[str]|None: List with surrounding whitespace stripped and empty items removed
        """
        normalized = [item.strip() for item in (keywords or []) if isinstance(item, str) and item.strip()]
        return normalized or None

    def __init__(self, config:dict=None):
        """FREEDOM log node
        Manages and stores log information in the system
        Args:
            config (dict): Settings
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
        self._task = asyncio.create_task(self._loop())
        self._logger = self.make_logger(__package__)
        self._logger.info(f"launch")
        repository.append(self)

    async def _loop(self):
        """Processing loop"""
        #TODO: システム終了時、最後までログを出力出来るようにする
        #TODO: ループ内でのエラー表示方法を考える
        temp_log_list:list[Column] = list()
        while sys.getrefcount(self) > 2:
            try:
                await asyncio.sleep(0)
                temp_log_list.extend(self._log_list)
                self._log_list.clear()
                if self._access and temp_log_list:
                    await self._access.insert(temp_log_list)
                    temp_log_list.clear()
            except asyncio.CancelledError:
                break
            except Exception:
                continue

    def make_logger(self, name:str, prefix:str=None) -> logic.Adapter:
        """Create a logger
        Args:
            name (str): Logger name
            prefix (str): Prefix
        Returns:
            logic.Adapter: Logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._stream_handler)
        logger.addHandler(self._output_handler)
        logger.propagate = False
        logger = logic.Adapter(logger, prefix)
        return logger

    async def fetch(self, begin_time:str, end_time:str, row_count:int|None=None, cursor_time:str|None=None, all_rows:bool=False, keywords:list[str]|None=None, levelnames:list[str]|None=None, sort_field:str="time", sort_direction:str="desc") -> list[dict]:
        """Get logs
        Args:
            begin_time (str): Start date/time
            end_time (str): End date/time
            row_count (int|None): Number of rows to fetch; None fetches all
            cursor_time (str|None): Reference time used when fetching additional rows
            all_rows (bool): True fetches all rows
            keywords (list[str]|None): List of keyword search conditions
            levelnames (list[str]|None): Log levels
            sort_field (str): Column to sort by
            sort_direction (str): Sort order (asc/desc)
        Returns:
            list[dict]: Logs
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
