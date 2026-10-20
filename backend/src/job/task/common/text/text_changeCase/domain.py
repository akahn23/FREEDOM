# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """text_changeCase task
    Args:
        type (str): Block type
        id (str): Block ID
        CASE (str): Operation mode
        TEXT (abstract.value.Domain): String to process
    """
    CASE: str = ""
    TEXT: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

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
            "type": "text_changeCase",
            "inputs": {
                "TEXT": {
                    "shadow": {
                        "type": "text",
                        "fields": {
                            "TEXT": "abc"
                        }
                    }
                }
            }
        }]
