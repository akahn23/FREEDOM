# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.text.text_isEmpty import Domain


class Logic(abstract.value.Logic[Domain]):
    """text_isEmpty task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._VALUE = await self.domain.VALUE.make_logic(self._job_id, self._logger)

    async def exec(self) -> bool:
        """Execute the task"""
        return not len(await self._VALUE.exec())
