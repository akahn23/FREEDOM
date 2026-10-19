# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """controls_for_customタスク ドメイン
    Attributes:
        type (str): タスク種類
        id (str): タスクID
        name (str): タスク名
            UIにタスク名として表示される内容
        next (Domain): 次タスク
        can_recover (bool): 復帰可能判定
            ジョブ停止時に復帰できる判定
        finished (bool): 終了フラグ
        command (list): コマンド内容
        should_log (bool): ログ出力判定
        VAR (dict[typing.Literal["id"], str]): 変数情報
        FROM (abstract.value.Domain): 開始値
        TO (abstract.value.Domain): 終了値
        BY (abstract.value.Domain): 増分値
        DO (abstract.statement.Domain): タスク内容
        DO_copy (dict): タスク内容のコピー
    """
    name: str = "範囲繰り返し"
    should_log: bool = False
    VAR: dict[typing.Literal["id"], str] = dataclasses.field(default_factory=dict)
    FROM: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    TO: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    BY: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    DO: abstract.statement.Domain = None
    DO_copy: dict = None

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if self.DO and self.DO_copy is None:
            self.DO_copy = dataclasses.asdict(self.DO)

    @classmethod
    def define_block(cls) -> list[dict]:
        """ブロック定義
        カスタムブロックの形状を定義する
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: ブロック定義
        """
        return [{
            'type': 'controls_for_custom',
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
            'message1': '%{BKY_CONTROLS_FOR_TITLE}',
            'args1': [
                {
                    'type': 'field_variable',
                    'name': 'VAR',
                    'variable': None,
                },
                {
                    'type': 'input_value',
                    'name': 'FROM',
                    'check': 'Number',
                    'align': 'RIGHT',
                },
                {
                    'type': 'input_value',
                    'name': 'TO',
                    'check': 'Number',
                    'align': 'RIGHT',
                },
                {
                    'type': 'input_value',
                    'name': 'BY',
                    'check': 'Number',
                    'align': 'RIGHT',
                },
            ],
            'message2': '%{BKY_CONTROLS_REPEAT_INPUT_DO} %1',
            'args2': [
                {
                    'type': 'input_statement',
                    'name': 'DO',
                },
            ],
            'inputsInline': True,
            'previousStatement': None,
            'nextStatement': None,
            'style': 'loop_blocks',
            'helpUrl': '%{BKY_CONTROLS_FOR_HELPURL}',
            'extensions': ['contextMenu_newGetVariableBlock', 'controls_for_tooltip'],
        }]

    @classmethod
    def define_toolbox(cls) -> list[dict]:
        """ツールボックス定義
        フィールド値や出力ブロックの初期値を定義する
        https://developers.google.com/blockly/guides/configure/web/toolboxes/category?hl=ja
        Returns:
            list[dict]: ツールボックス定義
        """
        return [{
            "kind": "block",
            "type": "controls_for_custom",
            "inputs": {
                "FROM": {
                    "shadow": {
                        "type": "math_number",
                        "fields": {
                            "NUM": 1
                        }
                    }
                },
                "TO": {
                    "shadow": {
                        "type": "math_number",
                        "fields": {
                            "NUM": 10
                        }
                    }
                },
                "BY": {
                    "shadow": {
                        "type": "math_number",
                        "fields": {
                            "NUM": 1
                        }
                    }
                },
            }
        }]
