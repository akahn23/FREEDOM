# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.infrastructure.lamp import Interface, NodeDomain


class Dummy(Interface):
    def __init__(self, domain:NodeDomain):
        """ランプダミー接続
        Args:
            domain (Domain): ドメイン
        """
        self._state = False

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
        return self._state

    async def write(self, address:int, data:bool):
        """書込み
        Args:
            address (int): アドレス
            data (bool): 書込み内容
        """
        self._state = data
