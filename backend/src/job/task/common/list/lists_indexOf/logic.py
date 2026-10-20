# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.list.lists_indexOf import Domain


class Logic(abstract.value.Logic[Domain]):
    """lists_indexOf task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._VALUE = await self.domain.VALUE.make_logic(self._job_id, self._logger)
        self._FIND = await self.domain.FIND.make_logic(self._job_id, self._logger) if self.domain.FIND else None

    async def exec(self) -> int:
        """Execute the task"""
        VALUE = list(await self._VALUE.exec())
        FIND = await self._FIND.exec() if self._FIND else []
        if FIND not in VALUE:
            return 0
        if self.domain.END == "FIRST":
            return VALUE.index(FIND) + 1
        elif self.domain.END == "LAST":
            return len(VALUE) - VALUE[::-1].index(FIND)
        else:
            raise ValueError(f"Unknown end: {self.domain.END}")
