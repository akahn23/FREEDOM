# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """text_join task
    Args:
        type (str): Task type
        id (str): Task ID
        ADD0 (abstract.value.Domain): Element 0
        ADD1 (abstract.value.Domain): Element 1
        ADD2 (abstract.value.Domain): Element 2
        ...
    """

    def __new__(cls, type:str, id=str, **kwargs):
        """Pre-instantiation processing
        Build and return a dataclass that includes the additional inputs
        Args:
            type (str): Task type
            id (str): Task ID
            name (str): Task name
            next (Domain): Next task
            can_recover (bool): Whether the task can be resumed
            finished (bool): Finished flag
            command (list): Command contents
        Returns:
            Domain: text_join task
        """
        fields = list()
        for k in kwargs.keys():
            if k.startswith("ADD"):
                fields.append((k, abstract.value.Domain, dataclasses.field(default=None)))
        domain = dataclasses.make_dataclass("Domain", fields, bases=(abstract.value.Domain,), namespace={
            'define_block': lambda cls: list(),
            'define_toolbox': lambda cls: list(),
        })
        return domain(type=type, id=id, **kwargs)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        Note:
            Defined by default
        """
        return []

    @classmethod
    def define_toolbox(cls) -> list[dict]:
        """Toolbox definition
        Define initial values for fields and output blocks
        https://developers.google.com/blockly/guides/configure/web/toolboxes/category?hl=ja
        Returns:
            list[dict]: Toolbox definitions
        """
        return [{
            "kind": "block",
            "type": "text_join"
        }]
