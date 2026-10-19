# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import equipment
from src.equipment.plc import Interface, NodeDomain
from src.repository import repository


class IoTDataShare(Interface):
    """PLC IoTDataShare接続
    Attributes:
        _domain (NodeDomain): ドメイン
    """
    def __init__(self, domain:NodeDomain):
        """インスタンス化
        Args:
            domain (NodeDomain): ドメイン
        """
        self._domain = domain

    async def close(self):
        """切断"""
        pass

    async def read_bit(self, address:int) -> bool:
        """ビットアドレス読込み
        Args:
            address (int): アドレス
        Returns:
            bool: 読込み結果
        """
        return await repository.retrieve(equipment.iotdatashare.Repository)[0].read_bit(self._domain.ip, address)

    async def write_bit(self, address:int, data:bool):
        """ビットアドレス書込み
        Args:
            address (int): アドレス
            data (bool): 書込み内容
        """
        await repository.retrieve(equipment.iotdatashare.Repository)[0].write_bit(self._domain.ip, address, data)

    async def read_word(self, address:int) -> int:
        """ワードアドレス読込み
        Args:
            address (int): アドレス
        Returns:
            int: 読込み結果
        """
        return await repository.retrieve(equipment.iotdatashare.Repository)[0].read(self._domain.ip, address)

    async def write_word(self, address:int, data:int):
        """ワードアドレス書込み
        Args:
            address (int): アドレス
            data (int): 書込み内容
        """
        await repository.retrieve(equipment.iotdatashare.Repository)[0].write(self._domain.ip, address, data)
