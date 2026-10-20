# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """lists_indexOf task
    Args:
        can_recover (bool): Whether the task can be resumed
        command (list[dict]): Command contents
        END (str): Origin
        VALUE (abstract.value.Domain): List to search
        FIND (abstract.value.Domain): Item to find
    """
    END: str = ""
    VALUE: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    FIND: abstract.value.Domain = None

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
            "type": "lists_indexOf",
            "inputs": {
                "VALUE": {
                    "shadow": {
                        "type": "_list_get"
                    }
                }
            }
        }]
