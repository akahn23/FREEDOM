# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src.infrastructure.shutter import Interface, NodeDomain


class Dummy(Interface):
    def __init__(self, domain:NodeDomain):
        """シャッターダミー接続
        Args:
            domain (Domain): ドメイン
        """
        self._domain = domain
        self._state = not self._domain.open_state
        self._task:asyncio.Task = None

    async def _open(self):
        """開くまでのディレイ処理"""
        if self._state != self._domain.open_state:
            await asyncio.sleep(3)
            self._state = self._domain.open_state

    async def close(self):
        """切断"""
        pass

    async def read(self) -> bool:
        """読込み
        Returns:
            bool: 読込み結果
        """
        return self._state

    async def write(self, data:bool):
        """書込み
        Args:
            data (bool): 書込み内容
        """
        if data:
            if not self._task or self._task.done():
                self._task = asyncio.create_task(self._open())
        else:
            self._task and self._task.cancel()
            self._state = not self._domain.open_state
