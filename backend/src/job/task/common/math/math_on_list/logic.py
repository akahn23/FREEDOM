# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import statistics
import random

from src.job.task import abstract
from src.job.task.common.math.math_on_list import Domain


class Logic(abstract.value.Logic[Domain]):
    """math_on_list task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._LIST = await self.domain.LIST.make_logic(self._job_id, self._logger) if self.domain.LIST else None

    async def exec(self) -> float | int:
        """Execute the task"""
        LIST = await self._LIST.exec() if self._LIST else []
        if self.domain.OP == "SUM":
            return sum(LIST)
        elif self.domain.OP == "MIN":
            return min(LIST)
        elif self.domain.OP == "MAX":
            return max(LIST)
        elif self.domain.OP == "AVERAGE":
            return statistics.mean(LIST)
        elif self.domain.OP == "MEDIAN":
            return statistics.median(LIST)
        elif self.domain.OP == "MODE":
            return statistics.multimode(LIST)
        elif self.domain.OP == "STD_DEV":
            return statistics.stdev(LIST)
        elif self.domain.OP == "RANDOM":
            return random.choice(LIST)
        else:
            raise ValueError(f"Unknown self.domain.OP: {self.domain.OP}")
