# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
from datetime import timedelta

from src.job.task import abstract
from src.job.task.common.control.controls_wait_logic import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Wait-for-condition task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._cond = await self.domain.cond.make_logic(self._job_id, self._logger)
        self._interval = await self.domain.interval.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        interval:timedelta = await self._interval.exec()
        while True:
            cond = await self._cond.exec()
            if self.domain.mode == "while" and not cond:
                break
            elif self.domain.mode == "until" and cond:
                break
            await asyncio.sleep(interval.total_seconds())
