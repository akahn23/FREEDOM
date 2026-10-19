# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.equipment.plc import Interface, NodeDomain


class Dummy(Interface):
    """PLC ダミー接続
    Attributes:
        _state (dict[str,int]): アドレスと値の辞書
    """
    def __init__(self, domain:NodeDomain):
        """インスタンス化
        Args:
            domain (NodeDomain): ドメイン
        """
        self._state:dict[str,int] = dict()

    async def close(self):
        """切断"""
        pass

    async def read_bit(self, address:str, bit:int) -> bool:
        """読込み
        Args:
            address (str): アドレス
            bit (int): ビット
        Returns:
            bool: 読込み結果
        """
        return bool((self._state.get(address, 0) >> bit) & 1)

    async def write_bit(self, address:str, bit:int, data:bool):
        """書込み
        Args:
            address (str): アドレス
            bit (int): ビット
            data (bool): 書込み内容
        """
        if address not in self._state.keys():
            self._state[address] = 0
        if data:
            self._state[address] = self._state[address] | (1 << bit)
        else:
            self._state[address] = self._state[address] & ~(1 << bit)

    async def read_word(self, address:str) -> int:
        """読込み
        Args:
            address (str): アドレス
        Returns:
            int: 読込み結果
        """
        return self._state.get(address, 0)

    async def write_word(self, address:str, data:int):
        """書込み
        Args:
            address (str): アドレス
            data (int): 書込み内容
        """
        if address not in self._state.keys():
            self._state[address] = 0
        self._state[address] = data
