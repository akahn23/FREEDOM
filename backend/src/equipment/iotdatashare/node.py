# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import aiohttp
import asyncio
import json

from src import abstract, freedom, util
from src.repository import repository
from src.equipment.iotdatashare import NodeDomain


class Node(abstract.Node, abstract.Lifecycle):
    def __init__(self, domain:NodeDomain):
        """IoT Data Shareノード
        Args:
            domain (NodeDomain): 設定
        """
        self.domain = domain
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__, f"[{self.domain.name}]")
        self._headers = {
            'Content-Type': 'application/json',
        }
        self._session = aiohttp.ClientSession(f'http://{domain.ip}:{domain.port}', timeout=aiohttp.ClientTimeout(total=domain.timeout))
        self._controller_lock:dict[str, asyncio.Lock] = dict()
        self.start()
        self._logger.info(f"launch: {self.domain=}")

    async def _loop(self):
        """更新ループ"""
        try:
            while self.running:
                await asyncio.gather(
                    self._update(),
                    asyncio.sleep(self.domain.update_cycle),
                )
        finally:
            await self._session.close()
            self._logger.info("close")

    async def _update(self):
        """定期更新処理
        接続対象リストを更新
        """
        try:
            self.domain.connect_list = await self._fetch_controller_names()
            for controller in self.domain.connect_list:
                if controller not in self._controller_lock:
                    self._controller_lock[controller] = asyncio.Lock()
            for lock in list(self._controller_lock.keys()):
                if lock not in self.domain.connect_list and not self._controller_lock[lock].locked():
                    self._controller_lock.pop(lock)
            self.domain.status = util.status.State.ACTIVE
        except Exception as e:
            self.domain.connect_list.clear()
            if self.domain.status != util.status.State.DISCONNECT:
                self._logger.error(f"Failed to update: {type(e)}-{e}")
            self.domain.status = util.status.State.DISCONNECT

    async def _fetch_controller_names(self):
        """接続対象リスト取得"""
        async with self._session.get("/api/v1/getcontrollernames", headers=self._headers) as resp:
            data = await resp.json()
            return data['names']

    async def _fetch_item_names(self, controller):
        """アイテムリスト取得"""
        async with self._session.get(f"/api/v1/getitemnames?controller={controller}", headers=self._headers) as resp:
            data = await resp.json()
            return data['names']

    async def _read(self, controller:str, item:str) -> int:
        """読込み
        Args:
            controller (str): 読込み先コントローラ
            item (str): 読込み先アイテム
        Returns:
            int: 読込み結果
        """
        item_list = await self._fetch_item_names(controller)
        if item in item_list:
            item_name = item
        elif f"[Read]{item}" in item_list:
            item_name = f"[Read]{item}"
        else:
            raise Exception(f"Failed to read: {item} dose not exist in {controller}")
        async with self._session.get(f"/api/v1//getvalue?controller={controller}&item={item_name}", headers=self._headers) as resp:
            resp.raise_for_status()
            resp_data = await resp.json()
            if not resp_data.get("success") or resp_data.get("result") == "NG":
                raise Exception(f"Failed to read: {resp_data=} {controller=} {item=}")
            return int(resp_data['value'])

    async def _write(self, controller:str, item:str, data:int):
        """書込み
        Args:
            controller (str): 書込み先コントローラ
            item (str): 書込み先アイテム
            data (int): 書込み内容
        """
        item_list = await self._fetch_item_names(controller)
        if item in item_list:
            item_name = item
        elif f"[Write]{item}" in item_list:
            item_name = f"[Write]{item}"
        else:
            raise Exception(f"Failed to write: {item} dose not exist in {controller}")
        send_data = {
            "controller": controller,
            "item": item_name,
            "value": data
        }
        async with self._session.post("/api/v1/putvalue", data=json.dumps(send_data), headers=self._headers) as resp:
            resp.raise_for_status()
            resp_data = await resp.json()
            if not resp_data.get("success") or resp_data.get("result") == "NG":
                raise Exception(f"Failed to write: {resp_data=} {controller=} {item=} {data=}")

    def close(self):
        """切断"""
        self.shutdown()

    async def read_item(self, controller:str, item:str) -> int:
        """アイテム読込み
        Args:
            controller (str): 読込み先コントローラ
            item (str): 読込み先アイテム
        Returns:
            int: 読込み結果
        """
        ret = await self._read(controller, item)
        return int(ret)

    async def write_item(self, controller:str, item:str, data:int):
        """アイテム書込み
        Args:
            controller (str): 書込み先コントローラ
            item (str): 書込み先アイテム
            data (int): 書込み内容
        """
        async with self._controller_lock[controller]:
            await self._write(controller, item, data)

    async def read_bit(self, controller:str, item:str, bit:int) -> bool:
        """ビット読込み
        Args:
            controller (str): 読込み先コントローラ
            item (str): 読込み先アイテム
            bit (int): ビット位置
        Returns:
            bool: 読込み結果
        """
        ret = await self._read(controller, item)
        return bool((ret >> bit) & 1)

    async def write_bit(self, controller:str, item:str, bit:int, data:bool):
        """ビット書込み
        Args:
            controller (str): 書込み先コントローラ
            item (str): 書込み先アイテム
            data (bool): 書込み内容
            bit (int): ビット位置
        """
        async with self._controller_lock[controller]:
            ret = await self._read(controller, item)
            if data:
                ret = ret | (1 << bit)
            else:
                ret = ret & ~(1 << bit)
            await self._write(controller, item, ret)
