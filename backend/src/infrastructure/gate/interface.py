# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src.infrastructure.gate import NodeDomain


class Interface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, domain:NodeDomain):
        """Gate connection interface
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
