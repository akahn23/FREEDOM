# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta

from src.job.task import abstract
from src.job.task.common.time.time_delta_duration import Domain


class Logic(abstract.value.Logic[Domain]):
    """Time set task logic"""
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        self._time = await self.domain.time.make_logic(self._job_id, self._logger)

    async def exec(self) -> timedelta:
        """Execute the task"""
        return timedelta(**{self.domain.unit: await self._time.exec()})
