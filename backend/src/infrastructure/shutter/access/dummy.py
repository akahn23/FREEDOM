# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src.infrastructure.shutter import NodeDomain, Interface


class Dummy(Interface):
    def __init__(self, domain:NodeDomain):
        """Shutter dummy connection
        Args:
            domain (Domain): Domain
        """
        self._domain = domain
        self._state = not self._domain.open_state
        self._task:asyncio.Task = None

    async def _open(self):
        """Delay before opening"""
        if self._state != self._domain.open_state:
            await asyncio.sleep(3)
            self._state = self._domain.open_state

    async def close(self):
        """Disconnect"""
        pass

    async def read(self) -> bool:
        """Read
        Returns:
            bool: Read result
        """
        return self._state

    async def write(self, data:bool):
        """Write
        Args:
            data (bool): Data to write
        """
        if data:
            if not self._task or self._task.done():
                self._task = asyncio.create_task(self._open())
        else:
            self._task and self._task.cancel()
            self._state = not self._domain.open_state
