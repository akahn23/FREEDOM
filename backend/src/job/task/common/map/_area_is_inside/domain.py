# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """Inside-area check task
    Args:
        type (str): Block type
        id (str): Block ID
        location (abstract.Domain): Location
        area_list (abstract.Domain) List of areas
    """
    location: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    area_list: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "_area_is_inside",
            "tooltip": "ロボットがエリア内にいるか判定する。",
            "message0": "%1 は %2 の内側",
            "args0": [
                {
                    "type": "input_value",
                    "name": "location",
                    "check": "Location"
                },
                {
                    "type": "input_value",
                    "name": "area_list",
                    "check": "Area",
                    "value": []
                },
            ],
            "output": "Boolean",
            "colour": 140,
            "inputsInline": True
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
            "type": "_area_is_inside",
            "inputs": {
                "location": {
                    "shadow": {
                        "type": "location_create"
                    }
                },
                "area_list": {
                    "shadow": {
                        "type": "_area_create"
                    }
                }
            }
        }]
