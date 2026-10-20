# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.list.lists_getIndex_custom import Domain


class Logic(abstract.value.Logic[Domain]):
    """lists_getIndex_custom task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._VALUE = await self.domain.VALUE.make_logic(self._job_id, self._logger)
        self._AT = await self.domain.AT.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        VALUE = list(await self._VALUE.exec())
        AT = int(await self._AT.exec())
        if self.domain.WHERE == "FROM_START":
            index = AT - 1
        elif self.domain.WHERE == "FROM_END":
            index = -AT
        else:
            raise ValueError(f"Unknown where: {self.domain.WHERE}")
        if self.domain.MODE == "GET":
            return VALUE[index]
        elif self.domain.MODE == "GET_REMOVE":
            return VALUE.pop(index)
        else:
            raise ValueError(f"Unknown mode: {self.domain.MODE}")
