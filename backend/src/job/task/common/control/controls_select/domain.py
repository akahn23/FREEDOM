# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Button selection task
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
        name (str): Task name
        var (dict[typing.Literal["id"], str]): Assignment target
        map (abstract.value.Domain): Dictionary of buttons and values to assign
    """
    name: str = "ボタン選択"
    var: dict[typing.Literal["id"], str] = dataclasses.field(default_factory=dict)
    map: abstract.value.Domain = None

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "controls_select",
            "tooltip": "押下したボタンに応じた内容を変数にセットする",
            "helpUrl": "",
            "message0": "%1 %2 %3 にセット %4 ボタン表示:選択内容 %5",
            "args0": [
                {
                    "type": "field_input",
                    "name": "name",
                    "text": cls.name
                },
                {"type": "input_dummy"},
                {
                    "type": "field_variable",
                    "name": "var",
                    "variable": "select"
                },
                {"type": "input_dummy", "align": "RIGHT"},
                {
                    "type": "input_value",
                    "name": "map",
                    "align": "RIGHT",
                    "check": "Dict"
                },
            ],
            "previousStatement": None,
            "nextStatement": None,
            "colour": 180
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
            "type": "controls_select",
            "inputs": {
                "map": {
                    "shadow": {
                        "type": "_dict_get",
                    }
                }
            }
        }]
