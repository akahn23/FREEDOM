# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.repository import repository
from src import freedom
from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Dummy placement task
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
    """
    name: str = "ダミー配置"
    robot: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    location: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "robot.dummy.place",
            "tooltip": "ダミーロボットを任意の座標に配置する",
            "helpUrl": "",
            "message0": "%1 %2 ロボット %3 位置 %4 ",
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
            "type": "robot.dummy.place",
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
                }
            }
        }]
