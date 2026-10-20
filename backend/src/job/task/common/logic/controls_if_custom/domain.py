# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Conditional branch task
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
        IF0 (abstract.value.Domain): Condition 0
        DO0 (abstract.statement.Domain): Statements 0
        IF1 (abstract.value.Domain): Condition 1
        DO1 (abstract.statement.Domain): Statements 1
        ...
        ELSE (abstract.statement.Domain): Else statements
    """
    name: str = "条件分岐"

    def __new__(cls, type:str, id=str, name="条件分岐", next=None, should_show=True, can_recover=True, finished=False, command=list(), **kwargs):
        """Pre-instantiation processing
        Build and return a dataclass that includes the additional inputs
        Args:
            type (str): Task type
            id (str): Task ID
            name (str): Task name
            next (Domain): Next task
            should_show (bool): Whether to display
            can_recover (bool): Whether the task can be resumed
            finished (bool): Finished flag
            command (list): Command contents
        Returns:
            Domain: Conditional branch task
        """
        fields = list()
        for k in kwargs.keys():
            if "IF" in k:
                fields.append((k, abstract.value.Domain, dataclasses.field(default_factory=abstract.value.Domain)))
            else:
                fields.append((k, abstract.statement.Domain, None))
        domain = dataclasses.make_dataclass("Domain", fields, bases=(abstract.statement.Domain,), namespace={
            'define_block': lambda cls: list(),
            'define_toolbox': lambda cls: list(),
        })
        return domain(type=type, id=id, name=name, next=next, should_show=should_show, can_recover=can_recover, finished=finished, command=command, **kwargs)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        Note:
            Changed from the default to set the task name
        """
        return [{
            'type': 'controls_if_custom',
            "message0": "%1 %2 タスク表示 %3",
            "args0": [
                {
                    "type": "field_input",
                    "name": "name",
                    "text": cls.name
                },
                {"type": "input_dummy"},
                {
                    "type": "field_checkbox",
                    "name": "should_show",
                    "checked": cls.should_show
                },
            ],
            'message1': '%{BKY_CONTROLS_IF_MSG_IF} %1',
            'args1': [
                {
                    'type': 'input_value',
                    'name': 'IF0',
                    'check': 'Boolean',
                },
            ],
            'message2': '%{BKY_CONTROLS_IF_MSG_THEN} %1',
            'args2': [
                {
                    'type': 'input_statement',
                    'name': 'DO0',
                },
            ],
            'previousStatement': None,
            'nextStatement': None,
            'style': 'logic_blocks',
            'helpUrl': '%{BKY_CONTROLS_IF_HELPURL}',
            'suppressPrefixSuffix': True,
            'mutator': 'controls_if_mutator',
            'extensions': ['controls_if_tooltip'],
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
            "type": "controls_if_custom"
        }]
