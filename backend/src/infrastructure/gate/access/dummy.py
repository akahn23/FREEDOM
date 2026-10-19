# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.infrastructure.gate import Interface, NodeDomain


class Dummy(Interface):
    def __init__(self, domain:NodeDomain):
        """遮断機ダミー接続
        Args:
            domain (Domain): ドメイン
        """
        self._domain = domain
        self.state = self._domain.open_state

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
        return self.state
