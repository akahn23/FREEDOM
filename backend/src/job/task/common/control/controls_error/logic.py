# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job import command
from src.job.task import abstract
from src.job.task.common.control.controls_error import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Error task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._error = await self.domain.error.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        error = await self._error.exec()
        self.domain.command.append(command.Text(error))
        raise RuntimeError(error)
