# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Infrastructure equipment handshake task
    Attributes:
        type (str): Task type
        id (str): Task ID
        name (str): Task name
            Text displayed as the task name in the UI
        next (Domain): Next task
        should_show (bool): Whether to display
            Whether to show the task in the UI
        can_recover (bool): Whether the task can be resumed
            Whether the job can be resumed after it is stopped
        finished (bool): Finished flag
        command (list): Command contents
        robot (abstract.value.Domain): Robot to coordinate
        exclude (abstract.value.Domain): Excluded equipment
        update_cycle (abstract.value.Domain): Update cycle
        warning_time (abstract.value.Domain): Time to wait for acceptance before warning
        task (abstract.statement.Domain): Subtask
    """
    name: str = "インフラ設備連携"
    should_show:bool = False
    can_recover:bool = False
    robot: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    exclude: abstract.value.Domain = None
    update_cycle: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    warning_time: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    task: abstract.statement.Domain = None

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "infrastructure.accept",
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
            "message1": "連携ロボット %1 除外設備 %2 更新周期 %3 許可待ち警告時間 %4 %5",
            "args1": [
                {
                    "type": "input_value",
                    "name": "robot",
                    "align": "RIGHT",
                    "check": "Robot"
                },
                {
                    "type": "input_value",
                    "name": "exclude",
                    "align": "RIGHT",
                    "check": ["Infrastructure", "Array"]
                },
                {
                    "type": "input_value",
                    "name": "update_cycle",
                    "align": "RIGHT",
                    "check": "TimeDelta"
                },
                {
                    "type": "input_value",
                    "name": "warning_time",
                    "align": "RIGHT",
                    "check": "TimeDelta"
                },
                {
                    "type": "input_statement",
                    "name": "task"
                }
            ],
            "previousStatement": None,
            "nextStatement": None,
            "colour": 60,
            "inputsInline": False,
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
            "type": "infrastructure.accept",
            "inputs": {
                "robot": {
                    "shadow": {
                        "type": "robot._get"
                    }
                },
                "update_cycle": {
                    "shadow": {
                        "type": "time_delta_duration",
                        "inputs": {
                            "time": {
                                "shadow": {
                                    "type": "math_number",
                                    "fields": {
                                        "NUM": 1
                                    }
                                }
                            },
                        },
                        "fields": {
                            "unit": "seconds",
                        }
                    }
                },
                "warning_time": {
                    "shadow": {
                        "type": "time_delta_duration",
                        "inputs": {
                            "time": {
                                "shadow": {
                                    "type": "math_number",
                                    "fields": {
                                        "NUM": 1
                                    }
                                }
                            },
                        },
                        "fields": {
                            "unit": "minutes",
                        }
                    }
                }
            }
        }]
