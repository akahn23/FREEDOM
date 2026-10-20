# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import robot
from src.job.task import abstract
from src.job.task.robot.dummy.is_dummy import Domain


class Logic(abstract.value.Logic[Domain]):
    """Task that gets a domain"""
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        self._robot = await self.domain.robot.make_logic(self._job_id, self._logger)

    async def exec(self) -> bool:
        """Execute the task"""
        return type(await self._robot.exec()) is robot.dummy.Node
