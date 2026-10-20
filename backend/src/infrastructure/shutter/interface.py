# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src.infrastructure.shutter import NodeDomain


class Interface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, domain: NodeDomain):
        """Shutter connection interface
        Args:
            domain (Domain): Domain
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def close(self):
        """Disconnect"""
        raise NotImplementedError()

    @abc.abstractmethod
    async def read(self) -> bool:
        """Read
        Returns:
            bool: Read result
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def write(self, data:bool):
        """Write
        Args:
            data (bool): Data to write
        """
        raise NotImplementedError()
