# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import equipment
from src.repository import repository
from src.infrastructure.lamp import NodeDomain, Interface


class IoTDataShare(Interface):
    def __init__(self, domain:NodeDomain):
        """Lamp IoTDataShare connection
        Args:
            domain (Domain): Domain
        """
        self._domain = domain

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
        str_address = f"DO{address}"
        data = await repository.retrieve(equipment.iotdatashare.Repository)[0].read(self._domain.ip, str_address)
        return bool(data)

    async def write(self, address:int, data:bool):
        """Write
        Args:
            address (int): Address
            data (bool): Data to write
        """
        str_address = f"DO{address}"
        await repository.retrieve(equipment.iotdatashare.Repository)[0].write(self._domain.ip, str_address, int(data))
