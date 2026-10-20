# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import random

from src.job.task import abstract
from src.job.task.common.math.math_random_int import Domain


class Logic(abstract.value.Logic[Domain]):
    """math_random_int task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._FROM = await self.domain.FROM.make_logic(self._job_id, self._logger)
        self._TO = await self.domain.TO.make_logic(self._job_id, self._logger)

    async def exec(self) -> int:
        """Execute the task"""
        FROM = int(await self._FROM.exec())
        TO = int(await self._TO.exec())
        return random.randint(FROM, TO)
