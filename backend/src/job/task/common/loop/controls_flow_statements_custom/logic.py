# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.loop.exception import LoopBreak, LoopContinue
from src.job.task.common.loop.controls_flow_statements_custom import Domain


class Logic(abstract.statement.Logic[Domain]):
    """controls_flow_statements_custom task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()

    async def exec(self):
        """Execute the task"""
        if self.domain.FLOW == "BREAK":
            raise LoopBreak()
        if self.domain.FLOW == "CONTINUE":
            raise LoopContinue()
