# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """ダミー配置タスク
    Args:
        type (str): タスク種類
        id (str): タスクID
        name (str): タスク名
            UIにタスク名として表示される内容
        next (Domain): 次タスク
        can_recover (bool): 復帰可能判定
            ジョブ停止時に復帰できる判定
        finished (bool): 終了フラグ
        command (list): コマンド内容
        robot (abstract.Domain): 対象ロボット
        location (abstract.Domain): 位置
    """
    name: str = "ダミー配置"
    robot: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    location: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """ブロック定義
        自作ブロックの形状を定義する
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: ブロック定義
        """
        return [{
            "type": "robot.dummy.place",
            "tooltip": "ダミーロボットを任意の座標に配置する",
            "helpUrl": "",
            "message0": "%1 %2 ロボット %3 位置 %4 ",
            "args0": [
                {
                    "type": "field_input",
                    "name": "name",
                    "text": cls.name
                },
                {"type": "input_dummy"},
                {
                    "type": "input_value",
                    "name": "robot",
                    "align": "RIGHT",
                    "check": "Robot"
                },
                {
                    'type': 'input_value',
                    'name': 'location',
                    "align": "RIGHT",
                    'check': 'Location',
                },
            ],
            "previousStatement": None,
            "nextStatement": None,
            "colour": 20,
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
            "type": "robot.dummy.place",
            "inputs": {
                "robot": {
                    "shadow": {
                        "type": "robot._get"
                    }
                },
                "location": {
                    "shadow": {
                        "type": "location_create"
                    }
                }
            }
        }]
