# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """controls_flow_statements_customタスク ドメイン
    Attributes:
        type (str): タスク種類
        id (str): タスクID
        name (str): タスク名
            UIにタスク名として表示される内容
        next (Domain): 次タスク
        should_show (bool): 表示判定
            ジョブ実行時に表示する判定
        can_recover (bool): 復帰可能判定
            ジョブ停止時に復帰できる判定
        finished (bool): 終了フラグ
        command (list): コマンド内容
        FLOW (typing.Literal["BREAK", "CONTINUE"]): ループ制御内容
    """
    name: str = "ループ制御"
    FLOW: typing.Literal["BREAK", "CONTINUE"] = "BREAK"

    @classmethod
    def define_block(cls) -> list[dict]:
        """ブロック定義
        カスタムブロックの形状を定義する
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: ブロック定義
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
        """ツールボックス定義
        フィールド値や出力ブロックの初期値を定義する
        https://developers.google.com/blockly/guides/configure/web/toolboxes/category?hl=ja
        Returns:
            list[dict]: ツールボックス定義
        """
        return [{
            "kind": "block",
            "type": "controls_flow_statements_custom",
        }]
