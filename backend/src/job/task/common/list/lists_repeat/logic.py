# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.list.lists_repeat import Domain


class Logic(abstract.value.Logic[Domain]):
    """lists_repeat task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._ITEM = await self.domain.ITEM.make_logic(self._job_id, self._logger) if self.domain.ITEM else None
        self._NUM = await self.domain.NUM.make_logic(self._job_id, self._logger)

    async def exec(self) -> list:
        """Execute the task"""
        item = list(await self._ITEM.exec()) if self._ITEM else None
        return [item] * int(await self._NUM.exec())
