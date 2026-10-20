# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.infrastructure.lamp import NodeDomain, Interface


class Dummy(Interface):
    def __init__(self, domain:NodeDomain):
        """Lamp dummy connection
        Args:
            domain (Domain): Domain
        """
        self._state = False

    async def close(self):
        """Disconnect"""
        pass

    async def read(self, address:int) -> bool:
        """Read
        Args:
            address (int): Address
        Returns:
            bool: Read result
        """
        return self._state

    async def write(self, address:int, data:bool):
        """Write
        Args:
            address (int): Address
            data (bool): Data to write
        """
        self._state = data
