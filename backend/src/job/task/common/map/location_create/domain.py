# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import freedom
from src.repository import repository
from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """Area set task
    Args:
        type (str): Block type
        id (str): Block ID
        location (list[float, float]) Location
    """
    location:list[float, float] = dataclasses.field(default_factory=list)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "location_create",
            "tooltip": "位置を地図上から指定して入力する。",
            "message0": "%1",
            "args0": [
                {
                    "type": "field_location",
                    "name": "location",
                    "value": repository.retrieve(freedom.map.Node)[0].domain.default_view.center
                },
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
            "kind": "block",
            "type": "location_create",
        }]
