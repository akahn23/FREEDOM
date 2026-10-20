# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """text_set task
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
        VAR (dict[typing.Literal["id"], str]): Variable
        VALUE (abstract.value.Domain): Value to assign
    """
    name: str = "テキストセット"
    VAR: dict[typing.Literal["id"], str] = dataclasses.field(default_factory=dict)
    VALUE: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "_text_set",
            'tooltip': '%{BKY_VARIABLES_SET_TOOLTIP}',
            'helpUrl': '%{BKY_VARIABLES_SET_HELPURL}',
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
            'message1': '%{BKY_VARIABLES_SET}',
            'args1': [
                {
                    'type': 'field_variable',
                    'name': 'VAR',
                    "variable": "string",
                    "variableTypes": ["String"],
                    "defaultType": "String"
                },
                {
                    'type': 'input_value',
                    'name': 'VALUE',
                    'check': 'String',
                },
            ],
            "previousStatement": None,
            "nextStatement": None,
            "inputsInline": True,
            'style': 'text_blocks'
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
            "type": "_text_set",
            "inputs": {
                "VALUE": {
                    "shadow": {
                        "type": "text"
                    }
                }
            }
        }]
