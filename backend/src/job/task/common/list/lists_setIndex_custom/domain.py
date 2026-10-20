# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """lists_setIndex_custom task
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
        LIST (abstract.value.Domain): Target list
        MODE (str): Operation mode
        WHERE (str): Origin
        AT (abstract.value.Domain): Number of elements from the origin
        TO (abstract.value.Domain): Value to set
    """
    name:str = "リスト変更"
    LIST: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    MODE: str = ""
    WHERE: str = ""
    AT: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    TO: abstract.value.Domain = None

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            "type": "lists_setIndex_custom",
            "tooltip": "",
            "helpUrl": "%{BKY_LISTS_SET_INDEX_HELPURL}",
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
            "message1": "%{BKY_LISTS_SET_INDEX_INPUT_IN_LIST} %1 %2 %3 %4 %5 %6 %{BKY_LISTS_SET_INDEX_INPUT_TO} %7",
            "args1": [
                {
                    "type": "input_value",
                    "name": "LIST",
                    "check": "Array"
                },
                {
                    "type": "field_dropdown",
                    "name": "MODE",
                    "options": [
                        ['%{BKY_LISTS_SET_INDEX_SET}', 'SET'],
                        ['%{BKY_LISTS_SET_INDEX_INSERT}', 'INSERT'],
                    ]
                },
                {"type": "input_dummy"},
                {
                    "type": "field_dropdown",
                    "name": "WHERE",
                    "options": [
                        ['%{BKY_LISTS_GET_INDEX_FROM_START}', 'FROM_START'],
                        ['%{BKY_LISTS_GET_INDEX_FROM_END}', 'FROM_END']
                    ]
                },
                {"type": "input_dummy"},
                {
                    "type": "input_value",
                    "name": "AT",
                    "check": "Number"
                },
                {
                    "type": "input_value",
                    "name": "TO"
                }
            ],
            "previousStatement": None,
            "nextStatement": None,
            "inputsInline": True,
            'style': 'list_blocks'
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
            "type": "lists_setIndex_custom",
            "inputs": {
                "LIST": {
                    "shadow": {
                        "type": "_list_get"
                    }
                },
                "AT": {
                    "shadow": {
                        "type": "math_number",
                        "fields": {
                            "NUM": 1
                        }
                    }
                }
            }
        }]
