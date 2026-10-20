# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
from datetime import timedelta

from src.job.task import abstract
from src.job.task.common.control.controls_wait_time import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Timed wait task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._interval = await self.domain.interval.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        interval:timedelta = await self._interval.exec()
        await asyncio.sleep(interval.total_seconds())
