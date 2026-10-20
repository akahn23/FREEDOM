# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.logic.logic_operation import Domain


class Logic(abstract.value.Logic[Domain]):
    """logic_operation task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._A = await self.domain.A.make_logic(self._job_id, self._logger) if self.domain.A else None
        self._B = await self.domain.B.make_logic(self._job_id, self._logger) if self.domain.B else None

    async def exec(self) -> bool:
        """Execute the task"""
        A = await self._A.exec() if self._A else None
        B = await self._B.exec() if self._B else None
        if self.domain.OP == "AND":
            return A and B
        elif self.domain.OP == "OR":
            return A or B
        else:
            raise ValueError(f"Unknown operator: {self.domain.OP}")
