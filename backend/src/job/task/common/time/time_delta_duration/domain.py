# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """Time-delta get task
    Args:
        type (str): Block type
        id (str): Block ID
        time (abstract.value.Domain): Input number
        unit (str): Time unit
    """
    time: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    unit:str = "seconds"

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "time_delta_duration",
            "tooltip": "時間の差分を取得する",
            "message0": "%1 %2 ",
            "args0": [
                {
                    "type": "input_value",
                    "name": "time",
                    "check": "Number"
                },
                {
                    "type": "field_dropdown",
                    "name": "unit",
                    "options": [["秒", "seconds"], ["分", "minutes"], ["時間", "hours"]]
                }
            ],
            "output": "TimeDelta",
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
            }
        }]
