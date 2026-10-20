# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """dict_get_item task
    Args:
        type (str): Block type
        id (str): Block ID
        DICT (abstract.value.Domain): Target dictionary
        MODE (str): Operation mode
        KEY (abstract.value.Domain): Key
    """
    DICT: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    MODE: str = "GET"
    KEY: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "dict_get_item",
            "tooltip": "辞書から索引の値を取得します",
            "helpUrl": "",
            "message0": "%1 %2 索引： %3",
            "args0": [
                {
                    "type": "input_value",
                    "name": "DICT",
                    "check": "Dict"
                },
                {
                    "type": "field_dropdown",
                    "name": "MODE",
                    "options": [
                        ['%{BKY_LISTS_GET_INDEX_GET}', 'GET'],
                        ['%{BKY_LISTS_GET_INDEX_GET_REMOVE}', 'GET_REMOVE']
                    ]
                },
                {
                    "type": "input_value",
                    "name": "KEY",
                }
            ],
            "output": None,
            "inputsInline": True,
            'colour': 280
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
            "type": "dict_get_item",
            "inputs": {
                "DICT": {
                    "shadow": {
                        "type": "_dict_get"
                    }
                },
                "KEY": {
                    "shadow": {
                        "type": "text"
                    }
                }
            }
        }]
