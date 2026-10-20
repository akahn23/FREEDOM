# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """controls_whileUntil_custom task domain
    Attributes:
        type (str): Task type
        id (str): Task ID
        name (str): Task name
            Text displayed as the task name in the UI
        next (Domain): Next task
        can_recover (bool): Whether the task can be resumed
            Whether the job can be resumed after it is stopped
        finished (bool): Finished flag
        command (list): Command contents
        should_log (bool): Whether to output logs
        MODE (str): Repeat mode
        BOOL (abstract.value.Domain): Repeat condition
        DO (abstract.statement.Domain): Task contents
        DO_copy (dict): Copy of the task contents
        condition (bool | None): Result of the repeat condition
    """
    name: str = "条件繰り返し"
    should_log: bool = False
    MODE: str = ""
    BOOL: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    DO: abstract.statement.Domain = None
    DO_copy: dict = None
    condition: bool | None = None

    def __post_init__(self):
        """Post-initialization processing"""
        super().__post_init__()
        if self.DO and self.DO_copy is None:
            self.DO_copy = dataclasses.asdict(self.DO)

    @classmethod
    def define_block(cls) -> list[dict]:
        """Block definition
        Define the shape of the custom block
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: Block definitions
        """
        return [{
            'type': 'controls_whileUntil_custom',
            'message0': '%1 %2 ログ出力 %3',
            'args0': [
                {
                    "type": "field_input",
                    "name": "name",
                    "text": cls.name
                },
                {"type": "input_dummy"},
                {
                    "type": "field_checkbox",
                    "name": "should_log",
                    "checked": cls.should_log
                },
            ],
            'message1': '%1 %2',
            'args1': [
                {
                    'type': 'field_dropdown',
                    'name': 'MODE',
                    'options': [
                        ['%{BKY_CONTROLS_WHILEUNTIL_OPERATOR_WHILE}', 'WHILE'],
                        ['%{BKY_CONTROLS_WHILEUNTIL_OPERATOR_UNTIL}', 'UNTIL'],
                    ],
                },
                {
                    'type': 'input_value',
                    'name': 'BOOL',
                    'check': 'Boolean',
                },
            ],
            'message2': '%{BKY_CONTROLS_REPEAT_INPUT_DO} %1',
            'args2': [
                {
                    'type': 'input_statement',
                    'name': 'DO',
                },
            ],
            'previousStatement': None,
            'nextStatement': None,
            'style': 'loop_blocks',
            'helpUrl': '%{BKY_CONTROLS_WHILEUNTIL_HELPURL}',
            'extensions': ['controls_whileUntil_tooltip'],
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
            "type": "controls_whileUntil_custom",
            "inputs": {
                "BOOL": {
                    "shadow": {
                        "type": "_logic_get"
                    }
                }
            }
        }]
