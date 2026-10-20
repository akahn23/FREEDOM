# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src import abstract, freedom, infrastructure, robot, util
from src.repository import repository
from src.infrastructure.shutter import NodeDomain, Interface, access
from src.infrastructure.command import Button


class Node(infrastructure.Node, abstract.Lifecycle):
    def __init__(self, domain:NodeDomain):
        """シャッター連携ノード
        Args:
            domain (NodeDomain): 設定
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
                    await self._access.write(False)
                    self._state = util.status.State.WAITING
                    self._logger.info("close")
            # 状態確認
            if await self._access.read() == self.domain.open_state:
                if self._state != util.status.State.ACTIVE:
                    self._logger.info("open")
                self._state = util.status.State.ACTIVE
            else:
                if self._state != util.status.State.WAITING:
                    self._logger.info("close")
                self._state = util.status.State.WAITING
                if self._related_robot:
                    await self._access.write(True)
        except Exception as e:
            if self._state != util.status.State.DISCONNECT:
                self._logger.error(f"disconnect {type(e)} - {e}")
            self._state = util.status.State.DISCONNECT

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
            Button(label="開ける", func="open"),
            Button(label="閉める", func="close"),
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
                await self._access.write(True)
            read_state = await self._access.read()
            if read_state == self.domain.open_state:
                if self._state != util.status.State.ACTIVE:
                    self._logger.info("open")
                self._state = util.status.State.ACTIVE
                return True
            else:
                return False
        else:
            await self.cancel(robot)
        return True

    async def cancel(self, robot:robot.Node[robot.Domain]) -> bool:
        """連携終了
        Args:
            robot (robot.Node): ロボットノード
        """
        if robot in self._related_robot:
            self._logger.info(f"exit: robot={robot.domain.name}")
            self._related_robot.remove(robot)
            if not self._related_robot:
                await self._access.write(False)
                self._state = util.status.State.WAITING
                self._logger.info("close")

    async def open(self):
        """ユーザ開き指示"""
        await self._access.write(True)
        self._logger.info(f"user open")

    async def close(self):
        """ユーザ閉じ指示"""
        self._related_robot.clear()
        await self._access.write(False)
        self._state = util.status.State.WAITING
        self._logger.info(f"user close")
