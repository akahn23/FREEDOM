# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import aiohttp
import json

from src.infrastructure.lamp import NodeDomain, Interface


class IoLogic(Interface):
    def __init__(self, domain:NodeDomain):
        """Lamp IoLogic connection
        Args:
            domain (Domain): Domain
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
        """Disconnect"""
        await self._session.close()

    async def read(self, address:int) -> bool:
        """Read
        Args:
            address (int): Address
        Returns:
            bool: Read result
        """
        async with self._session.get("/api/slot/0/io/do", headers=self._headers) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to read: {resp.status=} {resp.reason=}")
            ret = json.loads(await resp.text())
            return bool(ret['io']['do'][address]['doStatus'])

    async def write(self, address:int, data:bool):
        """Write
        Args:
            address (int): Address
            data (bool): Data to write
        """
        async with self._session.get("/api/slot/0/io/do", headers=self._headers) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to write: {resp.status=} {resp.reason=}")
            ret = json.loads(await resp.text())
        ret['io']['do'][address]['doStatus'] = int(data)
        async with self._session.put("/api/slot/0/io/do", data=json.dumps(ret), headers=self._headers) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to write: {resp.status=} {resp.reason=}")
