# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """dict_create_with task domain
    Args:
        type (str): Task type
        id (str): Task ID
        KEY0 (abstract.value.Domain): Key 0
        VALUE0 (abstract.value.Domain): Value 0
        KEY1 (abstract.value.Domain): Key 1
        VALUE1 (abstract.value.Domain): Value 1
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
            Domain: dict_create_with task domain
        """
        fields = list()
        for k in kwargs.keys():
            if k.startswith("KEY"):
                fields.append((k, abstract.value.Domain, dataclasses.field(default=None)))
            if k.startswith("VALUE"):
                fields.append((k, abstract.value.Domain, dataclasses.field(default=None)))
        domain = dataclasses.make_dataclass("Domain", fields, bases=(abstract.value.Domain,), namespace={
            'define_block': lambda sub_cls: cls.define_block(),
            'define_toolbox': lambda sub_cls: cls.define_toolbox(),
        })
        return domain(type=type, id=id, **kwargs)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "dict_create_with",
            "tooltip": "辞書を作成します",
            'message0': '',
            'args0': [],
            "mutator": "dict_create_with_mutator",
            'output': 'Dict',
            'colour': 280,
        }]

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
            "type": "dict_create_with",
            "extraState": {
                "itemCount": 2
            }
        }]
