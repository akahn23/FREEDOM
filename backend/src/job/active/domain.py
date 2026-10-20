# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import datetime
import typing

from src import abstract, job


@dataclasses.dataclass
class Variable:
    """Job variable
    Args:
        id (str): Block ID
        name (str): Name
        type (str): Type
        value (typing.Any): Value
    """
    id: str
    name: str
    type: str = None
    value: typing.Any = None


@dataclasses.dataclass
class NodeDomain:
    """Active job node settings
    Args:
        id (str): Node ID
        created_at (datetime.datetime): Creation date/time
        name (str): Name
        task (task.abstract.Domain): Task contents
        variables (Variable): Task variables
        command (Task): Task execution control
        error_msg (set): Error messages
        warning_msg (set): Warning messages
        visible (bool): Visibility flag
    """
    id:str
    created_at:datetime.datetime
    name:str
    task:job.task.abstract.statement.Domain
    variables:list[Variable]
    command:job.command.Task = None
    error_msg:set = dataclasses.field(default_factory=set)
    warning_msg:set = dataclasses.field(default_factory=set)
    visible:bool = True

    def __post_init__(self):
        """Post-initialization processing"""
        self.id = str(self.id)
        self.task = job.task.abstract.statement.Domain.to_domain(self.task)
        self.variables = [Variable(**v) for v in self.variables]
        if self.command is None:
            self.command = job.command.Task(id=self.task.id)
        elif type(self.command) is dict:
            self.command = job.command.Task(**self.command)
        self.error_msg = set(self.error_msg)
        self.warning_msg = set(self.warning_msg)


@dataclasses.dataclass
class Domain(abstract.database.Domain):
    """Active job settings
    Args:
        interface (str): Interface name
        dsn (str): Database connection string
        schema (str): Schema name
        table (str): Table name
        update_cycle (float): Update cycle
    """
    table:str = "job_active"

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return super().make_form(job.active.access)

    def __post_init__(self):
        """Post-initialization processing"""
        super().__post_init__(job.active.access)
