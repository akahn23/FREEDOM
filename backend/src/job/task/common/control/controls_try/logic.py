# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import copy

from src.job import command
from src.job.task import abstract
from src.job.task.common.control.controls_try import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Sequential exception-handling task logic"""
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        self._init_task = None
        self._try_task = None
        self._except_task = None
        self._finally_task = None
        if self.domain.init_task is not None:
            domain = copy.deepcopy(self.domain.init_task)
            self._init_task = await domain.make_logic(self._job_id, self._logger)
        if self.domain.try_task is not None:
            self._try_task = await self.domain.try_task.make_logic(self._job_id, self._logger)
            if not self.domain.command:
                self.domain.command.append(command.Task(self.domain.try_task.id))
        if self.domain.except_task is not None:
            domain = copy.deepcopy(self.domain.except_task)
            self._except_task = await domain.make_logic(self._job_id, self._logger)
        if self.domain.finally_task is not None:
            domain = copy.deepcopy(self.domain.finally_task)
            self._finally_task = await domain.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        try:
            if self._init_task is not None:
                self._logger.info(f"{self.domain.name} init_task start")
                init_task = command.Task(self.domain.init_task.id)
                await init_task.exec(self._init_task, self._logger)
            if self._try_task is not None:
                self._logger.info(f"{self.domain.name} try_task start")
                try_task:command.Task = self.domain.command[0]
                await try_task.exec(self._try_task, self._logger)
        except:
            if self._except_task is not None:
                self._logger.info(f"{self.domain.name} except_task start")
                except_task = command.Task(self.domain.except_task.id)
                await except_task.exec(self._except_task, self._logger)
            raise
        finally:
            if self._finally_task is not None:
                self._logger.info(f"{self.domain.name} finally_task start")
                finally_task = command.Task(self.domain.finally_task.id)
                await finally_task.exec(self._finally_task, self._logger)
