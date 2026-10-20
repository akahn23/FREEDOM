# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.math.math_modulo import Domain


class Logic(abstract.value.Logic[Domain]):
    """math_modulo task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._DIVIDEND = await self.domain.DIVIDEND.make_logic(self._job_id, self._logger)
        self._DIVISOR = await self.domain.DIVISOR.make_logic(self._job_id, self._logger)

    async def exec(self) -> int:
        """Execute the task
        Args:
            robot (robot.Node): Robot
        """
        DIVIDEND = await self._DIVIDEND.exec()
        DIVISOR = await self._DIVISOR.exec()
        return DIVIDEND % DIVISOR
