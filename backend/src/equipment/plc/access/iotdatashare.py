# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import equipment
from src.repository import repository
from src.equipment.plc import NodeDomain, Interface


class IoTDataShare(Interface):
    """PLC IoTDataShare connection
    Attributes:
        _domain (NodeDomain): Domain
    """
    def __init__(self, domain:NodeDomain):
        """Instantiate
        Args:
            domain (NodeDomain): Domain
        """
        self._domain = domain

    async def close(self):
        """Disconnect"""
        pass

    async def read_bit(self, address:int) -> bool:
        """Read a bit address
        Args:
            address (int): Address
        Returns:
            bool: Read result
        """
        return await repository.retrieve(equipment.iotdatashare.Repository)[0].read_bit(self._domain.ip, address)

    async def write_bit(self, address:int, data:bool):
        """Write a bit address
        Args:
            address (int): Address
            data (bool): Data to write
        """
        await repository.retrieve(equipment.iotdatashare.Repository)[0].write_bit(self._domain.ip, address, data)

    async def read_word(self, address:int) -> int:
        """Read a word address
        Args:
            address (int): Address
        Returns:
            int: Read result
        """
        return await repository.retrieve(equipment.iotdatashare.Repository)[0].read(self._domain.ip, address)

    async def write_word(self, address:int, data:int):
        """Write a word address
        Args:
            address (int): Address
            data (int): Data to write
        """
        await repository.retrieve(equipment.iotdatashare.Repository)[0].write(self._domain.ip, address, data)
