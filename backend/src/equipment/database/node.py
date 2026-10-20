# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src import abstract, freedom, util
from src.repository import repository
from src.equipment.database import NodeDomain, Interface, access


class Node(abstract.Node):
    """Database node
    Attributes:
        domain (NodeDomain): Domain
        _state (util.status.State): State
        _logger (freedom.log.Logger): Logger
        _access (Interface): Interface
        _task (asyncio.Task): Periodic processing task
    """
    def __init__(self, domain:NodeDomain):
        """Instantiate
        Args:
            domain (NodeDomain): Domain
        """
        self.domain = domain
        self._state = util.status.State.DISCONNECT
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__, f"[{self.domain.name}]")
        self._access:Interface = getattr(access, self.domain.interface)(self.domain)
        self._task = asyncio.create_task(self._loop())
        self._logger.info(f"launch: {self.domain=}")

    def close(self):
        """Disconnect"""
        self._task.cancel()

    def fetch_status(self) -> util.status.Status:
        """Get the status
        Returns:
            util.status.Status: Status
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
        """Insert or update
        Args:
            keys (list[str]): Match keys
            data (dict): Values to write
        """
        result = await self._access.upsert(keys=keys, data=data)
        self._logger.info(f"upsert: {keys=} {data=}")
        return result

    async def _loop(self):
        """Periodic processing"""
        try:
            while not await self._access.is_connected():
                await asyncio.sleep(self.domain.update_cycle)
            while True:
                await asyncio.gather(
                    self._update(),
                    asyncio.sleep(self.domain.update_cycle)
                )
        finally:
            await self._access.close()
            self._logger.info("end")

    async def _update(self):
        """Update the status"""
        if await self._access.is_connected():
            if self._state != util.status.State.WAITING:
                self._logger.info(f"connect")
                self._state = util.status.State.WAITING
        elif self._state != util.status.State.DISCONNECT:
            self._logger.error(f"disconnect")
            self._state = util.status.State.DISCONNECT
