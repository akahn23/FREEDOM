# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

from src.job.task import abstract
from src.job.task.common.time.time_delta_arithmetic import Domain


class Logic(abstract.value.Logic[Domain]):
    """Time difference calculation logic"""
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        self._LEFT = await self.domain.LEFT.make_logic(self._job_id, self._logger)
        self._RIGHT = await self.domain.RIGHT.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        LEFT:datetime = await self._LEFT.exec()
        RIGHT:datetime = await self._RIGHT.exec()
        operator = self.domain.operator
        try:
            if operator == "+":
                return LEFT + RIGHT
            if operator == "-":
                return LEFT - RIGHT
            if operator == "×":
                return LEFT * RIGHT
            if operator == "÷":
                return LEFT / RIGHT
        except Exception as e:
            self._logger.error(f"Failed to time_delta_arithmetic: {type(e)} - {e} {LEFT} {operator} {RIGHT}")
            raise Exception(f"時間計算の演算に失敗")
