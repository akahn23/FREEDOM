# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.logic.logic_negate import Domain


class Logic(abstract.value.Logic[Domain]):
    """logic_negate task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._BOOL = await self.domain.BOOL.make_logic(self._job_id, self._logger) if self.domain.BOOL else None

    async def exec(self) -> bool:
        """Execute the task"""
        BOOL = bool(await self._BOOL.exec()) if self._BOOL else None
        return not BOOL
