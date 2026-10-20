# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """Time arithmetic task
    Args:
        type (str): Block type
        id (str): Block ID
        LEFT (abstract.value.Domain): Left-hand value
        RIGHT (abstract.value.Domain): Right-hand value
        operator (str): Operator
    """
    LEFT: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    RIGHT: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    operator:str = "-"

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "time_delta_arithmetic",
            "tooltip": "日時や秒など、時間を扱う計算をする",
            "message0": "%1 %2 %3",
            "args0": [
                {
                    "type": "input_value",
                    "name": "LEFT",
                    "check": ["Time", "TimeDelta", "Number"]
                },
                {
                    "type": "field_dropdown",
                    "name": "operator",
                    "options": [["+", "+"], ["-", "-"], ["×", "×"], ["÷", "÷"]]
                },
                {
                    "type": "input_value",
                    "name": "RIGHT",
                    "check": ["Time", "TimeDelta", "Number"]
                },
            ],
            "inputsInline": True,
            "output": ["Time", "TimeDelta", "Number"],
            "colour": 310,
            "tooltip": "",
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
            "type": "time_delta_arithmetic",
            "fields": {
                "operator": cls.operator
            },
            "inputs": {
                "LEFT": {
                    "shadow": {
                        "type": "_time_now",
                    }
                },
                "RIGHT": {
                    "shadow": {
                        "type": "_time__get",
                    }
                }
            }
        }]
