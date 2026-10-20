# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src import abstract, freedom, infrastructure, robot, util
from src.repository import repository
from src.infrastructure.lamp import NodeDomain, Interface, access
from src.infrastructure.command import Button


class Node(infrastructure.Node, abstract.Lifecycle):
    """ランプ ノード
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
        self._related_robot:set[robot.Node[robot.Domain]] = set()
        self._state = util.status.State.WAITING
        self._access:Interface = getattr(access, self.domain.interface)(self.domain)
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
            # 連携確認
            if self._related_robot:
                for r in list(self._related_robot):
                    if not r.job or not util.map._is_inside(r.domain.location, self.domain.area_list):
                        self._related_robot.remove(r)
                        self._logger.info(f"exit: robot={r.domain.name}")
                if not self._related_robot:
                    await self._turn_off()
            # 状態確認
            if await self._access.read(self.domain.write_address):
                if self._state != util.status.State.ACTIVE:
                    self._logger.info("on")
                self._state = util.status.State.ACTIVE
            else:
                if self._state != util.status.State.WAITING:
                    self._logger.info("off")
                self._state = util.status.State.WAITING
                if self._related_robot:
                    await self._turn_on()
        except Exception as e:
            if self._state != util.status.State.DISCONNECT:
                self._logger.error(f"disconnect {type(e)} - {e}")
            self._state = util.status.State.DISCONNECT

    async def _turn_on(self):
        """点灯"""
        if self._state == util.status.State.ACTIVE:
            return
        await self._access.write(self.domain.write_address, True)
        self._state = util.status.State.ACTIVE
        self._logger.info(f"turn on")

    async def _turn_off(self):
        """消灯"""
        if self._state == util.status.State.WAITING:
            return
        await self._access.write(self.domain.write_address, False)
        self._state = util.status.State.WAITING
        self._logger.info(f"turn off")

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
            info.append(f"連携中ロボット:{[r.domain.name for r in self._related_robot]}")
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
        return [
            Button(label="点灯", func="turn_on"),
            Button(label="消灯", func="turn_off"),
        ]

    async def accept(self, robot:robot.Node[robot.Domain]) -> bool:
        """連携許可
        Args:
            robot (robot.Node): ロボット
        """
        if not robot.domain.location:
            return True
        if util.map._is_inside(robot.domain.location, self.domain.area_list):
            if robot not in self._related_robot:
                self._related_robot.add(robot)
                self._logger.info(f"entry: robot={robot.domain.name}")
            await self._turn_on()
        else:
            await self.cancel(robot)
        return True

    async def cancel(self, robot:robot.Node[robot.Domain]) -> bool:
        """連携終了
        Args:
            robot (robot.Node): ロボットノード
        """
        if robot in self._related_robot:
            self._related_robot.remove(robot)
            self._logger.info(f"exit: robot={robot.domain.name}")
            if not self._related_robot:
                await self._turn_off()
        return True

    async def turn_on(self):
        """UI点灯"""
        await self._access.write(self.domain.write_address, True)
        self._state = util.status.State.ACTIVE
        self._logger.info(f"user turn on")

    async def turn_off(self):
        """UI消灯"""
        await self._access.write(self.domain.write_address, False)
        self._state = util.status.State.WAITING
        self._logger.info(f"user turn off")
