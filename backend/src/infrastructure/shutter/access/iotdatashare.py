# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import equipment
from src.infrastructure.shutter import Interface, NodeDomain
from src.repository import repository


class IoTDataShare(Interface):
    def __init__(self, domain:NodeDomain):
        """シャッターIoTDataShare接続
        Args:
            domain (Domain): ドメイン
        """
        self._domain = domain

    async def close(self):
        """切断"""
        pass

    async def read(self) -> bool:
        """読込み
        Returns:
            bool: 読込み結果
        """
        str_address = f"DI{self._domain.read_address}"
        data = await repository.retrieve(equipment.iotdatashare.Repository)[0].read(self._domain.ip, str_address)
        return bool(data)

    async def write(self, data:bool):
        """書込み
        Args:
            data (bool): 書込み内容
        """
        str_address = f"DO{self._domain.write_address}"
        await repository.retrieve(equipment.iotdatashare.Repository)[0].write(self._domain.ip, str_address, int(data))
