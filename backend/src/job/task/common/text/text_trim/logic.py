# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.text.text_trim import Domain


class Logic(abstract.value.Logic[Domain]):
    """text_trim task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._TEXT = await self.domain.TEXT.make_logic(self._job_id, self._logger)

    async def exec(self) -> str:
        """Execute the task"""
        TEXT = str(await self._TEXT.exec())
        if self.domain.MODE == "BOTH":
            return TEXT.strip()
        elif self.domain.MODE == "LEFT":
            return TEXT.lstrip()
        elif self.domain.MODE == "RIGHT":
            return TEXT.rstrip()
        else:
            raise ValueError(f"Unknown mode: {self.domain.MODE}")
