# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import json

import aiohttp

from src.infrastructure.gate import Interface, NodeDomain


class IoLogic(Interface):
    def __init__(self, domain:NodeDomain):
        """遮断機IoLogic接続
        Args:
            domain (Domain): ドメイン
        """
        self._headers = {
            'Accept': 'vdn.dac.v1',
            'Content-Type': 'application/json',
        }
        self._session = aiohttp.ClientSession(
            f'http://{domain.ip}:{domain.port}',
            timeout=aiohttp.ClientTimeout(total=domain.timeout)
        )

    async def close(self):
        """切断"""
        await self._session.close()

    async def read(self, address:int) -> bool:
        """読込み
        Args:
            address (int): アドレス
        Returns:
            bool: 読込み結果
        """
        async with self._session.get("/api/slot/0/io/di", headers=self._headers) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to read: {resp.status=} {resp.reason=}")
            ret = json.loads(await resp.text())
            return bool(ret['io']['di'][address]['diStatus'])
