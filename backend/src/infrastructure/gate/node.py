# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src import abstract, freedom, infrastructure, robot, util
from src.repository import repository
from src.infrastructure.gate import NodeDomain, Interface, access
from src.infrastructure.command import Button


class Node(infrastructure.Node, abstract.Lifecycle):
    """遮断機 ノード
    Attributes:
        domain (NodeDomain): ドメイン
        _state (util.status.State): 状態
        _access (Interface): インターフェース
        _logger (freedom.log.Logger): ロガー
        _task (asyncio.Task): 定期処理タスク
    """
    def __init__(self, domain:NodeDomain):
        """インスタンス化
        Args:
            domain (NodeDomain): ドメイン
        """
        self.domain = domain
        self._state = util.status.State.WAITING
        self._access: Interface = getattr(access, self.domain.interface)(self.domain)
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__, f"[{self.domain.name}]")
        self.start()
        self._logger.info(f"launch: {self.domain=}")

    async def _loop(self):
        """定期ループ処理"""
        try:
            while self.running:
                await asyncio.gather(
                    asyncio.sleep(self.domain.update_cycle),
                    self._update(),
                )
        finally:
            await self._access.close()
            self._logger.info("end")

    async def _update(self):
        """状態更新"""
        try:
            await self._confirm()
        except Exception as e:
            if self._state != util.status.State.DISCONNECT:
                self._logger.error(f"disconnect {type(e)} - {e}")
            self._state = util.status.State.DISCONNECT

    async def _confirm(self) -> bool:
        """通行可能確認
        Returns:
            bool: 通行可能
        """
        if await self._access.read(self.domain.read_address) == self.domain.open_state:
            if self._state != util.status.State.ACTIVE:
                self._logger.info("open")
            self._state = util.status.State.ACTIVE
        else:
            if self._state != util.status.State.WAITING:
                self._logger.info("close")
            self._state = util.status.State.WAITING

    def fetch_status(self) -> util.status.Status:
        """状態取得
        Returns:
            util.status.Status: 状態
        """
        info = list()
        if self._state == util.status.State.DISCONNECT:
            state = util.status.State.ERROR
            info.append("【異常名】通信異常")
        else:
            state = self._state
        return util.status.Status(
            name=self.domain.name,
            state=state,
            location=self.domain.location,
            info=info,
        )

    def fetch_command(self) -> list:
        """手動操作取得
        Returns:
            list: 操作内容
        """
        if type(self._access) is access.Dummy:
            return [
                Button(label="開ける", func="set_state", kwargs={"state": self.domain.open_state}),
                Button(label="閉める", func="set_state", kwargs={"state": not self.domain.open_state}),
            ]
        else:
            return []

    async def accept(self, robot:robot.Node[robot.Domain]) -> bool:
        """連携許可
        Args:
            robot (robot.Node): ロボット
        """
        if not robot.domain.location:
            return True
        if util.map._is_inside(robot.domain.location, self.domain.area_list):
            await self._confirm()
            return self._state == util.status.State.ACTIVE
        else:
            return True

    async def cancel(self, robot:robot.Node[robot.Domain]) -> bool:
        """連携終了
        Args:
            robot (robot.Node): ロボットノード
        """
        pass

    def set_state(self, state:bool):
        """状態変更
        ダミーテスト用
        Args:
            state (bool): 状態
        """
        if type(self._access) is access.Dummy:
            self._access.state = state
            self._logger.info(f"set state: {state=}")
