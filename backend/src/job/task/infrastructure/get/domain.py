# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import infrastructure
from src.job.task import abstract
from src.repository import repository


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """インフラ設備取得タスク
    Args:
        type (str): ブロック種類
        id (str): ブロックID
        name (str): インフラ名
    """
    name: str = ""

    @classmethod
    def define_block(cls) -> list[dict]:
        """ブロック定義
        自作ブロックの形状を定義する
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: ブロック定義
        """
        option = [[i.domain.name, i.domain.name] for i in repository.retrieve(infrastructure.Node)]
        return [{
            "type": "infrastructure.get",
            "message0": "%1",
            "args0": [
                {
                    "type": "field_dropdown",
                    "name": "name",
                    "options": option if option else [["none", "none"]]
                }
            ],
            "output": "Infrastructure",
            "colour": 60,
            "tooltip": "",
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
            "type": "infrastructure.get"
        }]
