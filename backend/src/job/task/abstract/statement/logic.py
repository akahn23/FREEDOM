# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import typing

from src.job import command
from src.job.task import abstract
if typing.TYPE_CHECKING:
    from src.job.task.abstract.statement import Domain


class Logic[D:Domain](abstract.value.Logic[D], abc.ABC):
    """Abstract statement task logic
    Args:
        domain (D): Settings
        job_id (int): Job ID
        logger (logging.Logger): Logger
    """
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        if self.domain.next:
            self.next = await self.domain.next.make_logic(self._job_id, self._logger)
        else:
            self.next = None

    async def exec_command(self, command:typing.Any) -> typing.Any:
        """Execute a command
        Args:
            command (typing.Any): Command contents
        Returns:
            typing.Any: Execution result
        """
        self._logger.error(f"Failed to exec_command: name={self.domain.name=} {command=}")
        raise Exception(f"Failed to command")

    def retrieve_task(self, id:str|None=None) -> typing.Optional["Logic[Domain]"]:
        """Search tasks
        Args:
            id (str|None): Block ID
                None returns the running task
        Returns:
            Logic: Task
        """
        if self.domain.id == id:
            return self
        for cmd in self.domain.command:
            if not isinstance(cmd, command.Task):
                continue
            for logic in vars(self).values():
                if not isinstance(logic, abstract.statement.Logic):
                    continue
                if logic.domain.id != cmd.id:
                    continue
                if ret := logic.retrieve_task(id):
                    return ret
        if id is None and not self.domain.finished:
            return self
        if self.next is None:
            return None
        return self.next.retrieve_task(id)
