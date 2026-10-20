# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import inspect
import logging
import typing

from src.job import command
from src.job.task import abstract
from src.job.task.abstract.statement import Logic


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """Abstract statement task domain
    Blocks with top/bottom connections inherit from this
    Args:
        type (str): Task type
        id (str): Task ID
        name (str): Task name
            Text displayed as the task name in the UI
        next (Domain): Next task
        should_show (bool): Whether to display
            Whether to display while the job is running
        can_recover (bool): Whether the task can be resumed
            Whether the job can be resumed after it is stopped
        finished (bool): Finished flag
        command (list): Command contents
    """
    name:str
    next:typing.Optional['Domain'] = None
    should_show:bool = True
    can_recover:bool = True
    finished:bool = False
    command:list = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """Post-initialization processing"""
        super().__post_init__()
        self.command = self._to_command(self.command)

    def _to_command(self, cmd:list[dict]) -> list:
        """Convert to command classes
        Args:
            cmd (list[dict]): Before conversion
        Returns:
            list: After conversion
        """
        command_cls = inspect.getmembers(command, inspect.isclass)
        convert = {getattr(cls, "type"): cls for _, cls in command_cls if dataclasses.is_dataclass(cls)}
        return [convert[c.get("type")](**c) for c in cmd]

    async def make_logic(self, job_id:int, logger:logging.Logger) -> Logic:
        """Create the task logic class
        Args:
            job_id (int): Job ID
            logger (logging.Logger): Logger
        Returns:
            Logic: Task logic class
        """
        return await super().make_logic(job_id, logger)
