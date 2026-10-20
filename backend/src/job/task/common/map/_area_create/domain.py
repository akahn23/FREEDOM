# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """Area set task
    Args:
        type (str): Block type
        id (str): Block ID
        area_list (list[list[list[float]]]) List of areas
    """
    area_list:list[list[list[float]]] = dataclasses.field(default_factory=list)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "_area_create",
            "tooltip": "エリアを地図上で作成する。",
            "message0": "%1",
            "args0": [
                {
                    "type": "field_area",
                    "name": "area_list",
                    "value": []
                },
            ],
            "output": "Area",
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
            "kind": "block",
            "type": "_area_create",
        }]
