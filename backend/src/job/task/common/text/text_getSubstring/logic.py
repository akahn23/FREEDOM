# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.text.text_getSubstring import Domain


class Logic(abstract.value.Logic[Domain]):
    """text_getSubstring task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._STRING = await self.domain.STRING.make_logic(self._job_id, self._logger)
        self._AT1 = await self.domain.AT1.make_logic(self._job_id, self._logger)
        self._AT2 = await self.domain.AT2.make_logic(self._job_id, self._logger)

    async def exec(self) -> str:
        """Execute the task"""
        STRING = str(await self._STRING.exec())
        AT1 = int(await self._AT1.exec()) if self._AT1 else 1
        AT2 = int(await self._AT2.exec()) if self._AT2 else 1
        if self.domain.WHERE1 == "FROM_START":
            start = AT1 - 1
        elif self.domain.WHERE1 == "FROM_END":
            start = -AT1
        elif self.domain.WHERE1 == "FIRST":
            start = 0
        else:
            raise ValueError(f"Unknown where: {self.domain.WHERE1}")
        if self.domain.WHERE2 == "FROM_START":
            end = AT2
        elif self.domain.WHERE2 == "FROM_END":
            end = -AT2 + 1
            if end == 0:
                end = len(STRING)
        elif self.domain.WHERE2 == "LAST":
            end = len(STRING)
        else:
            raise ValueError(f"Unknown where: {self.domain.WHERE2}")
        return STRING[start:end]
