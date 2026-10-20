# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import typing
import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """controls_flow_statements_custom task domain
    Attributes:
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
        FLOW (typing.Literal["BREAK", "CONTINUE"]): Loop control action
    """
    name: str = "ループ制御"
    FLOW: typing.Literal["BREAK", "CONTINUE"] = "BREAK"

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            'type': 'controls_flow_statements_custom',
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
            'message1': '%1',
            'args1': [
                {
                    'type': 'field_dropdown',
                    'name': 'FLOW',
                    'options': [
                        ['%{BKY_CONTROLS_FLOW_STATEMENTS_OPERATOR_BREAK}', 'BREAK'],
                        ['%{BKY_CONTROLS_FLOW_STATEMENTS_OPERATOR_CONTINUE}', 'CONTINUE'],
                    ],
                },
            ],
            'previousStatement': None,
            'style': 'loop_blocks',
            'helpUrl': '%{BKY_CONTROLS_FLOW_STATEMENTS_HELPURL}',
            'suppressPrefixSuffix': True,
            'extensions': ['controls_flow_tooltip', 'controls_flow_in_loop_check'],
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
            "type": "controls_flow_statements_custom",
        }]
