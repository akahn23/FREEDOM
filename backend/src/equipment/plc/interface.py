# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src.equipment.plc import NodeDomain


class Interface(abc.ABC):
    """PLC interface"""
    @abc.abstractmethod
    def __init__(self, domain:NodeDomain):
        """Instantiate
        Args:
            domain (NodeDomain): Domain
        """
        raise NotImplementedError()

    async def close(self):
        """Disconnect"""
        pass

    @abc.abstractmethod
    async def read_bit(self, address: str, bit: int) -> bool:
        """Read a bit
        Args:
            address (str): Address
            bit (int): Bit
        Returns:
            bool: Read result
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def write_bit(self, address: str, bit: int, data: bool):
        """Write a bit
        Args:
            address (str): Address
            bit (int): Bit
            data (bool): Data to write
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def read_word(self, address: str) -> int:
        """Read a word
        Args:
            address (str): Address
        Returns:
            int: Read result
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def write_word(self, address: str, data: int):
        """Write a word
        Args:
            address (str): Address
            data (int): Data to write
        """
        raise NotImplementedError()
