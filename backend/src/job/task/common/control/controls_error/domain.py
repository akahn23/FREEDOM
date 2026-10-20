# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Error task
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
        error (abstract.value.Domain): Error name
    """
    name:str = "ジョブ異常"
    can_recover:bool = False
    error: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "controls_error",
            "tooltip": "任意のジョブ異常を発生させる",
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
            "message1": "異常名 %1",
            "args1": [
                {
                    "type": "input_value",
                    "align": "RIGHT",
                    "name": "error",
                    "check": "String"
                }
            ],
            "previousStatement": None,
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
            "type": "controls_error",
            "inputs": {
                "error": {
                    "shadow": {
                        "type": "text",
                        "fields": {
                            "TEXT": "タスク異常"
                        }
                    }
                }
            }
        }]
