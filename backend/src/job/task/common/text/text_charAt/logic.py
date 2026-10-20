# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import random
from src.job.task import abstract
from src.job.task.common.text.text_charAt import Domain


class Logic(abstract.value.Logic[Domain]):
    """text_charAt task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._VALUE = await self.domain.VALUE.make_logic(self._job_id, self._logger)
        self._AT = await self.domain.AT.make_logic(self._job_id, self._logger) if self.domain.AT else None

    async def exec(self):
        """Execute the task"""
        VALUE = str(await self._VALUE.exec())
        AT = int(await self._AT.exec()) if self._AT else 1
        if self.domain.WHERE == "FROM_START":
            return VALUE[AT - 1]
        elif self.domain.WHERE == "FROM_END":
            return VALUE[-AT]
        elif self.domain.WHERE == "FIRST":
            return VALUE[0]
        elif self.domain.WHERE == "LAST":
            return VALUE[-1]
        elif self.domain.WHERE == "RANDOM":
            return VALUE[int(random.random() * len(VALUE))]
        else:
            raise ValueError(f"Unknown where: {self.domain.WHERE}")
