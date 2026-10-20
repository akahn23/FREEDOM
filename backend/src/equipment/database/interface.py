# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src.equipment.database import NodeDomain


class Interface(abc.ABC):
    """Database interface"""
    @abc.abstractmethod
    def __init__(self, domain:NodeDomain):
        """Instantiate
        Args:
            domain (NodeDomain): Domain
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def close(self):
        """Disconnect"""
        raise NotImplementedError()

    @abc.abstractmethod
    async def is_connected(self) -> bool:
        """Check the connection
        Returns:
            bool: Connection state
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def upsert(self, keys:list[str], data:dict):
        """Insert or update
        Args:
            keys (list[str]): Match keys
            data (dict): Values to write
        """
        raise NotImplementedError()
