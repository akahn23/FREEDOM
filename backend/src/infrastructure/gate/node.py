# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import sys

from src import freedom, infrastructure, robot, util
from src.repository import repository
from src.infrastructure.gate import NodeDomain, Interface, access
from src.infrastructure.command import Button


class Node(infrastructure.Node):
    """Gate node
    Attributes:
        domain (NodeDomain): Domain
        _state (util.status.State): State
        _access (Interface): Interface
        _logger (freedom.log.Logger): Logger
        _task (asyncio.Task): Periodic processing task
    """
    def __init__(self, domain:NodeDomain):
        """Instantiate
        Args:
            domain (NodeDomain): Domain
        """
        self.domain = domain
        self._state = util.status.State.WAITING
        self._access: Interface = getattr(access, self.domain.interface)(self.domain)
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__, f"[{self.domain.name}]")
        self._task = asyncio.create_task(self._loop())
        self._logger.info(f"launch: {self.domain=}")

    async def _loop(self):
        """Periodic loop"""
        try:
            while sys.getrefcount(self) > 2:
                await asyncio.gather(
                    asyncio.sleep(self.domain.update_cycle),
                    self._update(),
                )
        finally:
            await self._access.close()
            self._logger.info("end")

    async def _update(self):
        """Update the status"""
        try:
            await self._confirm()
        except Exception as e:
            if self._state != util.status.State.DISCONNECT:
                self._logger.error(f"disconnect {type(e)} - {e}")
            self._state = util.status.State.DISCONNECT

    async def _confirm(self) -> bool:
        """Check whether passable
        Returns:
            bool: Passable
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
        """Get the status
        Returns:
            util.status.Status: Status
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
        """Get manual operations
        Returns:
            list: Operation contents
        """
        if type(self._access) is access.Dummy:
            return [
                Button(label="開ける", func="set_state", kwargs={"state": self.domain.open_state}),
                Button(label="閉める", func="set_state", kwargs={"state": not self.domain.open_state}),
            ]
        else:
            return []

    async def accept(self, robot:robot.Node[robot.Domain]) -> bool:
        """Grant infrastructure handshake permission to a robot
        Args:
            robot (robot.Node): Robot
        """
        if not robot.domain.location:
            return True
        if util.map._is_inside(robot.domain.location, self.domain.area_list):
            await self._confirm()
            return self._state == util.status.State.ACTIVE
        else:
            return True

    async def cancel(self, robot:robot.Node[robot.Domain]) -> bool:
        """End the infrastructure handshake for a robot
        Args:
            robot (robot.Node): Robot node
        """
        pass

    def set_state(self, state:bool):
        """Change the state
        For dummy testing
        Args:
            state (bool): State
        """
        if type(self._access) is access.Dummy:
            self._access.state = state
            self._logger.info(f"set state: {state=}")
