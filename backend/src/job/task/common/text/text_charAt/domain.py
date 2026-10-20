# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """text_charAt task
    Args:
        type (str): Block type
        id (str): Block ID
        WHERE (str): Origin
        VALUE (abstract.value.Domain): Target value
        AT (abstract.value.Domain): Number of elements from the origin
    """
    WHERE: str = ""
    VALUE: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    AT: abstract.value.Domain = None

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
            "type": "text_charAt",
            "inputs": {
                "VALUE": {
                    "shadow": {
                        "type": "_text_get"
                    }
                }
            }
        }]
