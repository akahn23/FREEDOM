# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import copy
import sys

from src import repository, freedom, job
from src.job.active import Node, Domain, Interface


class Repository(repository.Repository[Node]):
    def __init__(self, config:dict):
        """Active job repository
        Args:
            config (dict): Settings
        """
        # 設定更新時は旧リポジトリを削除
        if old := repository.repository.retrieve(self.__class__):
            repository.repository.remove(old[0])
            old[0]._task.cancel()
        super().__init__()
        self.domain = Domain(**config)
        self._access:Interface = getattr(job.active.access, self.domain.interface)(self.domain)
        self._logger = repository.repository.retrieve(freedom.log.Node)[0].make_logger(__name__)
        self._task = asyncio.create_task(self._loop())
        self._prev_data = list()
        self._logger.info(f"launch: {self.domain}")
        repository.repository.append(self)

    async def _loop(self):
        """Update loop"""
        await self._init_node()
        try:
            while sys.getrefcount(self) > 2:
                await asyncio.gather(
                    self._update(),
                    asyncio.sleep(0),
                )
        finally:
            for node in self.data:
                node.cancel()

    async def _init_node(self):
        """Initial build of active job nodes
        Builds the nodes remaining in the database
        """
        while True:
            try:
                config_list = await self._access.fetch()
                break
            except Exception:
                await asyncio.sleep(self.domain.update_cycle)
        for config in config_list:
            try:
                self.data.append(Node(config))
            except Exception as e:
                self._logger.error(f"Failed to make job: {type(e)} - {e} {config=}")

    async def _update(self):
        """Update
        Updates the database if a node has changed
        """
        try:
            current = [node.domain for node in self.data]
            if current != self._prev_data:
                await self._access.update(current)
                self._prev_data = copy.deepcopy(current)
        except Exception as e:
            if self._prev_data:
                self._logger.error(f"update error: {type(e)} - {e}")
            self._prev_data.clear()

    async def insert(self, name:str, task:dict, variables:list[dict]) -> str:
        """Add an active job
        Args:
            name (str): Job name
            task (dict): Task contents
            variables (list[dict]): Task variables
        Returns:
            str: Job ID
        """
        config = await self._access.insert(name, task, variables)
        self.data.append(Node(config))
        return str(config["id"])
