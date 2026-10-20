# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

from src.job import command
from src.job.task import abstract
from src.job.task.common.loop.exception import LoopBreak, LoopContinue
from src.job.task.common.loop.controls_whileUntil_manual import Domain


class Logic(abstract.statement.Logic[Domain]):
    """controls_whileUntil_manual task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        logger = self._logger if self.domain.should_log else logging.getLogger("loop")
        self._DO = await self.domain.DO.make_logic(self._job_id, logger) if self.domain.DO else None
        if not self.domain.command:
            self.domain.command.append(command.Switch(self.domain.label_on, self.domain.label_off, True))
            if self.domain.DO:
                self.domain.command.append(command.Task(self.domain.DO.id))

    async def exec(self):
        """Execute the task"""
        logger = self._logger if self.domain.should_log else logging.getLogger("loop")
        while True:
            try:
                if len(self.domain.command) > 1:
                    task:command.Task = self.domain.command[1]
                    await task.exec(self._DO, logger)
            except LoopBreak:
                break
            except LoopContinue:
                pass
            if not self.domain.command[0].value:
                break
            self.domain.DO = abstract.statement.Domain.to_domain(self.domain.DO_copy) if self.domain.DO_copy else None
            self._DO = await self.domain.DO.make_logic(self._job_id, logger) if self.domain.DO else None
            await asyncio.sleep(0)
        self.domain.command.clear()

    async def exec_command(self, command:bool):
        """Execute a command
        Args:
            command (bool): Command contents
        """
        if type(command) is bool:
            self.domain.command[0].value = command
        else:
            await super().exec_command(command)
