# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from typing import Any
from src.job.task import abstract
from src.job.task.common.logic.logic_ternary import Domain


class Logic(abstract.value.Logic[Domain]):
    """logic_ternary task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._IF = await self.domain.IF.make_logic(self._job_id, self._logger) if self.domain.IF else None
        self._THEN = await self.domain.THEN.make_logic(self._job_id, self._logger) if self.domain.THEN else None
        self._ELSE = await self.domain.ELSE.make_logic(self._job_id, self._logger) if self.domain.ELSE else None

    async def exec(self) -> Any:
        """Execute the task"""
        IF = await self._IF.exec() if self._IF else None
        THEN = await self._THEN.exec() if self._THEN else None
        ELSE = await self._ELSE.exec() if self._ELSE else None
        return THEN if IF else ELSE
