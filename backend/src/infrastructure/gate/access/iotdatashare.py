# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import equipment
from src.infrastructure.gate import Interface, NodeDomain
from src.repository import repository


class IoTDataShare(Interface):
    def __init__(self, domain:NodeDomain):
        """遮断機IoTDataShare接続
        Args:
            domain (Domain): ドメイン
        """
        self._domain = domain

    async def close(self):
        """切断"""
        pass

    async def read(self, address:int) -> bool:
        """読込み
        Args:
            address (int): アドレス
        Returns:
            bool: 読込み結果
        """
        str_address = f"DI{address}"
        data = await repository.retrieve(equipment.iotdatashare.Repository)[0].read(self._domain.ip, str_address)
        return bool(data)
