# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.list.lists_sort import Domain


class Logic(abstract.value.Logic[Domain]):
    """lists_sort task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._LIST = await self.domain.LIST.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        LIST = list(await self._LIST.exec())
        DIRECTION = self.domain.DIRECTION == "-1"
        if self.domain.TYPE == "NUMERIC":
            return sorted(LIST, key=float, reverse=DIRECTION)
        elif self.domain.TYPE == "TEXT":
            return sorted(LIST, key=str, reverse=DIRECTION)
        elif self.domain.TYPE == "IGNORE_CASE":
            return sorted(LIST, key=lambda s: str(s).lower(), reverse=DIRECTION)
        else:
            raise ValueError(f"Unknown mode: {self.domain.TYPE}")
