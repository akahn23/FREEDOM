# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import equipment
from src.repository import repository
from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """Database write task
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
        node (str): Node name
        keys (abstract.value.Domain): Match keys
        data (abstract.value.Domain): Values to write
    """
    name: str = "DB書込み"
    node: str = ""
    keys: abstract.value.Domain = None
    data: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        options = [[node.domain.name, node.domain.name] for node in repository.retrieve(equipment.database.Node)]
        return [{
            "type": "equipment.database.upsert",
            "tooltip": "指定したデータベースに対して書込みを行う",
            "helpUrl": "",
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
            "message1": "%1 %2 一致キー %3 書込み内容 %4",
            "args1": [
                {
                    "type": "field_dropdown",
                    "name": "node",
                    "options": options or [["設定なし", "none"]]
                },
                {"type": "input_dummy", "align": "RIGHT"},
                {
                    "type": "input_value",
                    "name": "keys",
                    "align": "RIGHT",
                    "check": ["String", "Array"]
                },
                {
                    "type": "input_value",
                    "name": "data",
                    "align": "RIGHT",
                    "check": "Dict"
                }
            ],
            "previousStatement": None,
            "nextStatement": None,
            "colour": 90
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
            "type": "equipment.database.upsert",
            "inputs": {
                "data": {
                    "shadow": {
                        "type": "_dict_get"
                    }
                }
            }
        }]
