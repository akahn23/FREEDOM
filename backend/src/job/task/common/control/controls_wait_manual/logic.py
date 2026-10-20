# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src.job import command
from src.job.task import abstract
from src.job.task.common.control.controls_wait_manual import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Manual wait task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._label = await self.domain.label.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        self.domain.command.clear()
        try:
            label = await self._label.exec()
            self.domain.command.append(command.Button(label, label))
            while self.domain.command:
                await asyncio.sleep(0)
        finally:
            self.domain.command.clear()

    async def exec_command(self, command:str):
        """Execute a command
        Args:
            command (str): Command contents
        """
        if command == await self._label.exec():
            self.domain.command.clear()
        else:
            await super().exec_command(command)
