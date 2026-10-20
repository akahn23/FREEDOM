# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import math

from src.job.task import abstract
from src.job.task.common.math.math_round import Domain


class Logic(abstract.value.Logic[Domain]):
    """math_round task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._NUM = await self.domain.NUM.make_logic(self._job_id, self._logger)

    async def exec(self) -> int:
        """Execute the task"""
        OP = self.domain.OP
        NUM = await self._NUM.exec()
        if OP == "ROUND":
            return round(NUM)
        elif OP == "ROUNDUP":
            return math.ceil(NUM)
        elif OP == "ROUNDDOWN":
            return math.floor(NUM)
        else:
            raise ValueError(f"Unknown OP: {OP}")
