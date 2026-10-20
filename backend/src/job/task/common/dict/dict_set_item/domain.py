# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """dict_set_item task
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
        DICT (abstract.value.Domain): Variable
        KEY (abstract.value.Domain): Value to assign
        VALUE (abstract.value.Domain): Value to assign
    """
    name: str = "辞書変更"
    DICT: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    KEY: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    VALUE: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "dict_set_item",
            'tooltip': '辞書に値をセットします',
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
            'message1': '辞書 %1 索引 %2 に値 %3 をセット ',
            'args1': [
                {
                    'type': 'input_value',
                    'name': 'DICT',
                    "check": "Dict"
                },
                {
                    'type': 'input_value',
                    'name': 'KEY',
                },
                {
                    'type': 'input_value',
                    'name': 'VALUE',
                },
            ],
            "previousStatement": None,
            "nextStatement": None,
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
            "type": "dict_set_item",
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
                },
            }
        }]
