# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.repository import repository
from src import freedom
from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Dummy move task
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
        robot (abstract.Domain): Target robot
        location (abstract.Domain): Location
        speed (abstract.Domain): Speed (km/s)
        stop (abstract.Domain): Stop condition
    """
    name: str = "ダミー移動"
    robot: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    location: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    meter: str = "1000"
    second: str = "3600"
    speed: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    stop: abstract.value.Domain = None

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "robot.dummy.move",
            "tooltip": "ダミーロボットを任意の座標に移動する",
            "helpUrl": "",
            "message0": "%1 %2 ロボット %3 位置 %4 速度( %5 / %6 ) %7 停止条件 %8",
            "args0": [
                {
                    "type": "field_input",
                    "name": "name",
                    "text": cls.name
                },
                {"type": "input_dummy"},
                {
                    "type": "input_value",
                    "name": "robot",
                    "align": "RIGHT",
                    "check": "Robot"
                },
                {
                    'type': 'input_value',
                    'name': 'location',
                    "align": "RIGHT",
                    'check': 'Location',
                },
                {
                    "type": "field_dropdown",
                    "name": "meter",
                    "options": [
                        [ "km", "1000" ],
                        [ "m", "1" ],
                        [ "mm", "0.001" ]
                    ]
                },
                {
                    "type": "field_dropdown",
                    "name": "second",
                    "options": [
                        [ "h", "3600" ],
                        [ "m", "60" ],
                        [ "s", "1" ]
                    ]
                },
                {
                    "type": "input_value",
                    "name": "speed",
                    "align": "RIGHT",
                    "check": "Number"
                },
                {
                    "type": "input_value",
                    "name": "stop",
                    "align": "RIGHT",
                    "check": "Boolean"
                }
            ],
            "previousStatement": None,
            "nextStatement": None,
            "colour": 20,
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
            "type": "robot.dummy.move",
            "inputs": {
                "robot": {
                    "shadow": {
                        "type": "robot._get"
                    }
                },
                "location": {
                    "shadow": {
                        "type": "location_create"
                    }
                },
                "speed": {
                    "shadow": {
                        "type": "math_number",
                        "fields": {
                            "NUM": 10
                        }
                    }
                }
            }
        }]
