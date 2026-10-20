# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Log output task
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
        message (abstract.value.Domain): Log message
        level (str): Log level
    """
    name: str = "ログ表示"
    message: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    level: str = "INFO"

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "controls_log",
            "tooltip": "ログメッセージを表示する",
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
            "message1": "%1 %2",
            "args1": [
                {
                    "type": "field_dropdown",
                    "name": "level",
                    "options": [
                        ["DEBUG", "DEBUG"],
                        ["INFO", "INFO"],
                        ["WARNING", "WARNING"],
                        ["ERROR", "ERROR"]
                    ]
                },
                {
                    "type": "input_value",
                    "align": "RIGHT",
                    "name": "message",
                    "check": "String"
                }
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
            "type": "controls_log",
            "fields": {
                "level": "INFO"
            },
            "inputs": {
                "message": {
                    "shadow": {
                        "type": "text",
                        "fields": {
                            "TEXT": "メッセージ"
                        }
                    }
                }
            }
        }]
