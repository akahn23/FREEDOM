# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Wait-for-condition task
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
        mode (typing.Literal["while", "until"]): Wait mode
        cond (abstract.value.Domain): Condition
        interval (abstract.value.Domain): Check interval
    """
    name: str = "条件待機"
    mode: typing.Literal["while", "until"] = "while"
    cond: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    interval: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "controls_wait_logic",
            "tooltip": "条件が揃うまでジョブを待機させる",
            "helpUrl": "",
            "message0": "%1 %2 %3 %4 確認周期 %5",
            "args0": [
                {
                    "type": "field_input",
                    "name": "name",
                    "text": cls.name
                },
                {"type": "input_dummy"},
                {
                    "type": "field_dropdown",
                    "name": "mode",
                    "options": [
                        ["待機を続ける条件", "while"],
                        ["待機が終わる条件", "until"]
                    ]
                },
                {
                    "type": "input_value",
                    "align": "RIGHT",
                    "name": "cond",
                    "check": "Boolean"
                },
                {
                    "type": "input_value",
                    "align": "RIGHT",
                    "name": "interval",
                    "check": "TimeDelta"
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
            "type": "controls_wait_logic",
            "inputs": {
                "cond": {
                    "shadow": {
                        "type": "_logic_get"
                    }
                },
                "interval": {
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
                            }
                        },
                        "fields": {
                            "unit": "seconds"
                        }
                    }
                }
            }
        }]
