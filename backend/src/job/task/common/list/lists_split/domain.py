# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """lists_split task
    Args:
        type (str): Block type
        id (str): Block ID
        MODE (str): SPLIT or JOIN
        INPUT (abstract.value.Domain): Target value
        DELIM (abstract.value.Domain): Delimiter
    """
    MODE: str = ""
    INPUT: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    DELIM: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        Note:
            Defined by default
        """
        return []

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
            "type": "lists_split",
            "inputs": {
                "INPUT": {
                    "shadow": {
                        "type": "_text_get"
                    }
                },
                "DELIM": {
                    "shadow": {
                        "type": "text",
                        "fields": {
                            "TEXT": ","
                        }
                    }
                }
            }
        }]
