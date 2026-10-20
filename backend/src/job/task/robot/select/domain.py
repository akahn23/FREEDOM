# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Robot selection task
    Args:
        type (str): Task type
        id (str): Task ID
        name (str): Task name
            Text displayed as the task name in the UI
        next (Domain): Next task
        can_recover (bool): Whether the task can be resumed
            Whether the job can be resumed after it is stopped
        finished (bool): Finished flag
        command (list): Command contents
        VAR (dict[typing.Literal["id"], str]): Variable
        condition (abstract.value.Domain): Display condition
    """
    name: str = "ロボット選択"
    VAR: dict[typing.Literal["id"], str] = dataclasses.field(default_factory=dict)
    condition: abstract.value.Domain = None

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "robot.select",
            "tooltip": "ロボット選択ボタンを表示する",
            "helpUrl": "",
            "message0": "%1 %2 %3 にセット %4 表示条件 %5",
            "args0": [
                {
                    "type": "field_input",
                    "name": "name",
                    "text": cls.name
                },
                {"type": "input_dummy"},
                {
                    "type": "field_variable",
                    "name": "VAR",
                    "variable": "robot",
                    "variableTypes": ["Robot"],
                    "defaultType": "Robot"
                },
                {"type": "input_dummy", "align": "RIGHT"},
                {
                    "type": "input_value",
                    "name": "condition",
                    "align": "RIGHT",
                    "check": "Boolean"
                },
            ],
            "previousStatement": None,
            "nextStatement": None,
            "colour": 30
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
            "type": "robot.select"
        }]
