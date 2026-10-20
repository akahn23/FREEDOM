# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.map.location_create import Domain


class Logic(abstract.value.Logic[Domain]):
    """Location set task logic"""
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()

    async def exec(self) -> list[float, float]:
        """Execute the task"""
        return self.domain.location