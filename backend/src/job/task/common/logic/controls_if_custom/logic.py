# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job import command
from src.job.task import abstract
from src.job.task.common.logic.controls_if_custom import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Conditional branch task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        for k,v in vars(self.domain).items():
            if k == "next" or not isinstance(v, abstract.value.Domain):
                continue
            setattr(self, k, await v.make_logic(self._job_id, self._logger))

    async def exec(self):
        """Execute the task"""
        if not self.domain.command:
            for name, logic in vars(self).items():
                if "IF" not in name:
                    continue
                if hasattr(self, f"DO{name[2:]}") and await logic.exec():
                    do:abstract.statement.Logic = getattr(self, f"DO{name[2:]}")
                    self.domain.command.append(command.Task(do.domain.id))
                    break
            else:
                if hasattr(self, "ELSE"):
                    do:abstract.statement.Logic = getattr(self, "ELSE")
                    self.domain.command.append(command.Task(do.domain.id))
        if self.domain.command:
            task:command.Task = self.domain.command[0]
            for logic in vars(self).values():
                if isinstance(logic, abstract.statement.Logic) and logic.domain.id == task.id:
                    await task.exec(logic, self._logger)
                    return
