# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import logging
import typing

from src.job.task.abstract import statement


@dataclasses.dataclass
class Task:
    """Task command
    Args:
        id (str): ID of the first task
        type (str): Command type
    """
    id:str
    type:str = "task"

    async def exec(self, task:statement.Logic[statement.Domain], logger:logging.Logger):
        """Execute the task
        Args:
            task (statement.Logic[statement.Domain]): Task
            logger (logging.Logger): Logger
        """
        while task:
            if not task.domain.finished:
                logger.info(f"task exec: name={task.domain.name}, type={task.domain.type}")
                await task.exec()
                task.domain.finished = True
            task = task.next

    def recover(self, task:statement.Domain|None, id:str, finished:bool=True) -> bool:
        """Resume a task
        Recursive function
        Args:
            task (statement.Domain|None): Task contents
            id (str): ID of the task to resume
            finished (bool): Task finished
        Returns:
            bool: Task finished
        """
        if task is None:
            return finished
        if task.id == id:
            if not task.can_recover:
                raise Exception(f"{task.name} cannot recover")
            finished = False
        sub_finished = finished
        for cmd in task.command:
            if not isinstance(cmd, Task):
                continue
            for sub_task in vars(task).values():
                if not isinstance(sub_task, statement.Domain):
                    continue
                if sub_task.id != cmd.id:
                    continue
                if not self.recover(sub_task, id, finished):
                    sub_finished = False
        if not finished:
            task.command.clear()
        task.finished = finished and sub_finished
        return self.recover(task.next, id, task.finished)


@dataclasses.dataclass
class Button:
    """Button command
    Args:
        label (str): Display text
        value (typing.Any): Response value
        type (str): Command type
    """
    label:str
    value:typing.Any
    type:str = "button"

@dataclasses.dataclass
class Switch:
    """Switch command
    Args:
        label_on(str): Text shown when ON
        label_off(str): Text shown when OFF
        value (bool): Response value
        type (str): Command type
    """
    label_on:str
    label_off:str
    value:bool
    type:str = "switch"

@dataclasses.dataclass
class Text:
    """Text command
    Args:
        label (str): Display text
        type (str): Command type
    """
    label:str
    type:str = "text"
