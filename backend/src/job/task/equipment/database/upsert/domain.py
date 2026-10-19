# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import equipment
from src.job.task import abstract
from src.repository import repository


@dataclasses.dataclass
class Domain(abstract.statement.Domain):
    """DB書込みタスク
    Args:
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
        node (str): ノード名
        keys (abstract.value.Domain): 一致キー
        data (abstract.value.Domain): 書込み値
    """
    name: str = "DB書込み"
    node: str = ""
    keys: abstract.value.Domain = None
    data: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)

    @classmethod
    def define_block(cls) -> list[dict]:
        """ブロック定義
        自作ブロックの形状を定義する
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: ブロック定義
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
        """ツールボックス定義
        フィールド値や出力ブロックの初期値を定義する
        https://developers.google.com/blockly/guides/configure/web/toolboxes/category?hl=ja
        Returns:
            list[dict]: ツールボックス定義
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
