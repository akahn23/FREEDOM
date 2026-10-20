# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.equipment.database import NodeDomain
from src.equipment.database.interface import Interface


class Dummy(Interface):
    """Database dummy connection
    Attributes:
        data (list[dict]): Data
    """
    def __init__(self, domain:NodeDomain):
        """Instantiate
        Args:
            domain (NodeDomain): Domain
        """
        self.data:list[dict] = list()

    async def close(self):
        """Disconnect"""
        pass

    async def is_connected(self) -> bool:
        """Check the connection
        Returns:
            bool: Connection state
        """
        return True

    async def upsert(self, keys:list[str], data:dict):
        """Insert or update
        Args:
            keys (list[str]): Match keys
            data (dict): Values to write
        """
        if keys:
            for i, d in enumerate(self.data):
                if all(d.get(k) == data.get(k) for k in keys):
                    self.data[i] = data
                    return
        self.data.append(data)
