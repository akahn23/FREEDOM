# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src.infrastructure.lamp import NodeDomain


class Interface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, domain:NodeDomain):
        """Lamp connection interface
        Args:
            domain (Domain): Domain
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def close(self):
        """Disconnect"""
        raise NotImplementedError()

    @abc.abstractmethod
    async def read(self, address:int) -> bool:
        """Read
        Args:
            address (int): Address
        Returns:
            bool: Read result
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def write(self, address:int, data:bool):
        """Write
        Args:
            address (int): Address
            data (bool): Data to write
        """
        raise NotImplementedError()
