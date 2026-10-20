# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import dataclasses
import importlib
import inspect
import logging
import typing

from src.job import task
from src.job.task.abstract.value import Logic


@dataclasses.dataclass
class Domain(abc.ABC):
    """Abstract value task domain
    Blocks with an output connection inherit from this
    Args:
        type (str): Block type
        id (str): Block ID
    """
    type:str
    id:str

    def __post_init__(self):
        """Post-initialization processing
        Converts any class variables of type Domain
        """
        for field in dataclasses.fields(self):
            if not getattr(self, field.name):
                continue
            if field.name == "next" or inspect.isclass(field.type) and issubclass(field.type, Domain):
                setattr(self, field.name, Domain.to_domain(getattr(self, field.name)))

    @classmethod
    def to_domain(cls, content:dict) -> typing.Optional['Domain']:
        """Convert a task domain
        Converts database-stored contents into a domain
        Args:
            contents (dict): Database-stored contents
        Returns:
            Domain: Task domain
        """
        for _, common in inspect.getmembers(task.common, inspect.ismodule):
            for name, module in inspect.getmembers(common, inspect.ismodule):
                if name == content["type"]:
                    return getattr(module, "Domain")(**content)
        module = importlib.import_module(f"src.job.task.{content["type"]}")
        return getattr(module, "Domain")(**content)

    async def make_logic(self, job_id:int, logger:logging.Logger) -> Logic:
        """Create the task logic class
        Args:
            job (active): Job ID
            logger (logging.Logger): Logger
        Returns:
            Logic: Task logic class
        """
        for _, common in inspect.getmembers(task.common, inspect.ismodule):
            for name, module in inspect.getmembers(common, inspect.ismodule):
                if name == self.type:
                    logic:Logic = getattr(module, "Logic")(self, job_id, logger)
                    await logic.init()
                    return logic
        module = importlib.import_module(f"src.job.task.{self.type}")
        logic:Logic = getattr(module, "Logic")(self, job_id, logger)
        await logic.init()
        return logic

    @classmethod
    @abc.abstractmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        raise NotImplementedError("Subclasses must implement define_block method")

    @classmethod
    @abc.abstractmethod
    def define_toolbox(cls) -> list[dict]:
        """Toolbox definition
        Define initial values for fields and output blocks
        https://developers.google.com/blockly/guides/configure/web/toolboxes/category?hl=ja
        Returns:
            list[dict]: Toolbox definitions
        """
        raise NotImplementedError("Subclasses must implement define_block method")
