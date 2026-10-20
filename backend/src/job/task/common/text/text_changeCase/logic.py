# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.text.text_changeCase import Domain


class Logic(abstract.value.Logic[Domain]):
    """text_changeCase task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._TEXT = await self.domain.TEXT.make_logic(self._job_id, self._logger)

    async def exec(self) -> str:
        """Execute the task"""
        text = str(await self._TEXT.exec())
        if self.domain.CASE == "UPPERCASE":
            return text.upper()
        elif self.domain.CASE == "LOWERCASE":
            return text.lower()
        elif self.domain.CASE == "TITLECASE":
            return text.title()
        else:
            raise ValueError(f"Unknown case: {self.domain.CASE}")
