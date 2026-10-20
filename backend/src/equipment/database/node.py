# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src import abstract, freedom, util
from src.repository import repository
from src.equipment.database import NodeDomain, Interface, access


class Node(abstract.Node, abstract.Lifecycle):
    """データベース ノード
    Attributes:
        domain (NodeDomain): ドメイン
        _state (util.status.State): 状態
        _logger (freedom.log.Logger): ロガー
        _access (Interface): インターフェース
        _task (asyncio.Task): 定期処理タスク
    """
    def __init__(self, domain:NodeDomain):
        """インスタンス化
        Args:
            domain (NodeDomain): ドメイン
        """
        self.domain = domain
        self._state = util.status.State.DISCONNECT
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__, f"[{self.domain.name}]")
        self._access:Interface = getattr(access, self.domain.interface)(self.domain)
        self.start()
        self._logger.info(f"launch: {self.domain=}")

    def close(self):
        """切断"""
        self.shutdown()

    def fetch_status(self) -> util.status.Status:
        """状態取得
        Returns:
            util.status.Status: 状態
        """
        if self._state == util.status.State.DISCONNECT:
            state = util.status.State.ERROR
            info = ["通信異常"]
        else:
            state = self._state
            info = []
        return util.status.Status(
            name=self.domain.name,
            state=state,
            location=self.domain.location,
            info=info,
        )

    async def upsert(self, keys:list[str], data:dict):
        """追加・更新
        Args:
            keys (list[str]): 一致キー
            data (dict): 書込み値
        """
        result = await self._access.upsert(keys=keys, data=data)
        self._logger.info(f"upsert: {keys=} {data=}")
        return result

    async def _loop(self):
        """定期処理"""
        try:
            while not await self._access.is_connected():
                await asyncio.sleep(self.domain.update_cycle)
            while self.running:
                await asyncio.gather(
                    self._update(),
                    asyncio.sleep(self.domain.update_cycle)
                )
        finally:
            await self._access.close()
            self._logger.info("end")

    async def _update(self):
        """状態更新"""
        if await self._access.is_connected():
            if self._state != util.status.State.WAITING:
                self._logger.info(f"connect")
                self._state = util.status.State.WAITING
        elif self._state != util.status.State.DISCONNECT:
            self._logger.error(f"disconnect")
            self._state = util.status.State.DISCONNECT
