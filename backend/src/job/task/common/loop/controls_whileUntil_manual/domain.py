# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """controls_whileUntil_manual task domain
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
        label_on (str): Text shown when ON
        label_off (str): Text shown when OFF
        DO (abstract.statement.Domain): Task contents
        DO_copy (dict): Copy of the task contents
    """
    name: str = "手動繰り返し"
    should_log: bool = True
    label_on: str = ""
    label_off: str = ""
    DO: abstract.statement.Domain = None
    DO_copy: dict = None

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
            'type': 'controls_whileUntil_manual',
            "tooltip": "スイッチがONの間、タスクを繰り返し実行する",
            "helpUrl": "",
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
            'message1': 'ON表示 : %1 %2 OFF表示: %3 %4 %{BKY_CONTROLS_REPEAT_INPUT_DO} %5',
            'args1': [
                {
                    "type": "field_input",
                    "name": "label_on",
                    "text": "繰り返す"
                },
                {"type": "input_dummy"},
                {
                    "type": "field_input",
                    "name": "label_off",
                    "text": "この週で終了"
                },
                {"type": "input_dummy"},
                {
                    'type': 'input_statement',
                    'name': 'DO',
                },
            ],
            'previousStatement': None,
            'nextStatement': None,
            'style': 'loop_blocks',
            "inputsInline": False,
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
            "type": "controls_whileUntil_manual",
        }]
