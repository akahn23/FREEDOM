# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.job.active import exception
from src.job.task.job.active.result import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Return value task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._result = None
        if self.domain.result:
            self._result = await self.domain.result.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        if self._result:
            ret = await self._result.exec()
            self._logger.info(f"result={ret}")
            raise exception.Result(ret)
        else:
            raise exception.Result(None)
