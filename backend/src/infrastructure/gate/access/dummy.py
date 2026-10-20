# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.infrastructure.gate import NodeDomain, Interface


class Dummy(Interface):
    def __init__(self, domain:NodeDomain):
        """Gate dummy connection
        Args:
            domain (Domain): Domain
        """
        self._domain = domain
        self.state = self._domain.open_state

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
        return self.state
