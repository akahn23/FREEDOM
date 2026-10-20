# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import infrastructure
from src.repository import repository
from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """Infrastructure equipment get task
    Args:
        type (str): Block type
        id (str): Block ID
        name (str): Infrastructure name
    """
    name: str = ""

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        option = [[i.domain.name, i.domain.name] for i in repository.retrieve(infrastructure.Node)]
        return [{
            "type": "infrastructure.get",
            "message0": "%1",
            "args0": [
                {
                    "type": "field_dropdown",
                    "name": "name",
                    "options": option if option else [["none", "none"]]
                }
            ],
            "output": "Infrastructure",
            "colour": 60,
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
            "type": "infrastructure.get"
        }]
