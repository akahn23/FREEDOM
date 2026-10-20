# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """Location variable get task
    Args:
        type (str): Block type
        id (str): Block ID
        VAR (dict[typing.Literal["id"], str]): Source variable
    """
    VAR: dict[typing.Literal["id"], str] = dataclasses.field(default_factory=dict)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "_location_get",
            "tooltip": "%{BKY_VARIABLES_GET_TOOLTIP}",
            "helpUrl": "%{BKY_VARIABLES_GET_HELPURL}",
            "message0": "%1",
            "args0": [
                {
                    "type": "field_variable",
                    "name": "VAR",
                    "variable": "location",
                    "variableTypes": ["Location"],
                    "defaultType": "Location"
                }
            ],
            "output": "Location",
            "colour": 140,
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
            "kind": "sep",
            "gap": "48"
        },{
            "kind": "button",
            "text": "%{BKY_NEW_VARIABLE}",
            "callbackKey": "createVariable_Location"
        },{
            "kind": "block",
            "type": "_location_get"
        }]
