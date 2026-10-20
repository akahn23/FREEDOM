# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.equipment.plc import NodeDomain, Interface


class Dummy(Interface):
    """PLC dummy connection
    Attributes:
        _state (dict[str,int]): Dictionary of addresses and values
    """
    def __init__(self, domain:NodeDomain):
        """Instantiate
        Args:
            domain (NodeDomain): Domain
        """
        self._state:dict[str,int] = dict()

    async def close(self):
        """Disconnect"""
        pass

    async def read_bit(self, address:str, bit:int) -> bool:
        """Read
        Args:
            address (str): Address
            bit (int): Bit
        Returns:
            bool: Read result
        """
        return bool((self._state.get(address, 0) >> bit) & 1)

    async def write_bit(self, address:str, bit:int, data:bool):
        """Write
        Args:
            address (str): Address
            bit (int): Bit
            data (bool): Data to write
        """
        if address not in self._state.keys():
            self._state[address] = 0
        if data:
            self._state[address] = self._state[address] | (1 << bit)
        else:
            self._state[address] = self._state[address] & ~(1 << bit)

    async def read_word(self, address:str) -> int:
        """Read
        Args:
            address (str): Address
        Returns:
            int: Read result
        """
        return self._state.get(address, 0)

    async def write_word(self, address:str, data:int):
        """Write
        Args:
            address (str): Address
            data (int): Data to write
        """
        if address not in self._state.keys():
            self._state[address] = 0
        self._state[address] = data
