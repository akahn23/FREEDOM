# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.repository import repository
from src import equipment
from src.job.task import abstract
from src.job.task.equipment.database.upsert import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Write task logic"""
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        self._keys_logic = None
        if self.domain.keys is not None:
            self._keys_logic = await self.domain.keys.make_logic(self._job_id, self._logger)
        self._data_logic = await self.domain.data.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        keys = await self._keys_logic.exec() if self._keys_logic else list()
        if isinstance(keys, str):
            keys = [keys]
        if node := repository.retrieve(equipment.database.Node, name=self.domain.node):
            try:
                await node[0].upsert(keys, await self._data_logic.exec())
            except Exception as e:
                self._logger.error(f"DB書込み失敗: {type(e)} - {e}")
                raise RuntimeError(f"DB書込み失敗")
        else:
            raise RuntimeError(f"DBノードが見つかりません: {self.domain.node}")
