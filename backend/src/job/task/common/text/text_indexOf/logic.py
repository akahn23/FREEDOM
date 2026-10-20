# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.text.text_indexOf import Domain


class Logic(abstract.value.Logic[Domain]):
    """text_indexOf task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._VALUE = await self.domain.VALUE.make_logic(self._job_id, self._logger)
        self._FIND = await self.domain.FIND.make_logic(self._job_id, self._logger)

    async def exec(self) -> int:
        """Execute the task"""
        VALUE = str(await self._VALUE.exec())
        FIND = str(await self._FIND.exec())
        if self.domain.END == "FIRST":
            return VALUE.find(FIND) + 1
        elif self.domain.END == "LAST":
            return VALUE.rfind(FIND) + 1
        else:
            raise ValueError(f"Unknown end: {self.domain.END}")
