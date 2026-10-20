# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """PLC write task
    Args:
        type (str): Task type
        id (str): Task ID
        name (str): Task name
            Text displayed as the task name in the UI
        next (Domain): Next task
        should_show (bool): Whether to display
            Whether to display while the job is running
        can_recover (bool): Whether the task can be resumed
            Whether the job can be resumed after it is stopped
        finished (bool): Finished flag
        command (list): Command contents
        plc_address (abstract.value.Domain): PLC address
        data (abstract.value.Domain): Data to write
    """
    name:str = "PLC書込み"
    plc_address: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    data: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "equipment.plc.write",
            "tooltip": "PLCに指定した値を書き込む",
            "message0": "%1 %2 タスク表示 %3",
            "args0": [
                {
                    "type": "field_input",
                    "name": "name",
                    "text": cls.name
                },
                {"type": "input_dummy"},
                {
                    "type": "field_checkbox",
                    "name": "should_show",
                    "checked": cls.should_show
                },
            ],
            "message1": "アドレス %1 書込み内容 %2",
            "args1": [
                {
                    "type": "input_value",
                    "name": "plc_address",
                    "align": "RIGHT",
                    "check": "EquipmentPLC"
                },
                {
                    "type": "input_value",
                    "name": "data",
                    "align": "RIGHT",
                    "check": ["Boolean", "Number"]
                },
            ],
            "colour": 90,
            "previousStatement": None,
            "nextStatement": None,
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
            "type": "equipment.plc.write",
            "inputs": {
                "plc_address": {
                    "shadow": {
                        "type": "equipment.plc.get_address"
                    }
                },
                "data": {
                    "shadow": {
                        "type": "logic_boolean"
                    }
                }
            }
        }]
