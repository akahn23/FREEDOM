# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """Dummy check task
    Args:
        type (str): Block type
        id (str): Block ID
        robot (abstract.value.Domain): Input robot
    """
    robot: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "robot.dummy.is_dummy",
            "tooltip": "入力ロボットがダミーかを判定します",
            "helpUrl": "",
            "message0": "%1 はダミー",
            "args0": [
                {
                    "type": "input_value",
                    "name": "robot",
                    "check": "Robot"
                },
            ],
            "output": "Boolean",
            "colour": 20
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
            "type": "robot.dummy.is_dummy",
            "inputs": {
                "robot": {
                    "shadow": {
                        "type": "robot._get"
                    }
                }
            }
        }]
