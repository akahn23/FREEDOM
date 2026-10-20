# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """時間計算タスク
    Args:
        type (str): ブロック種類
        id (str): ブロックID
        LEFT (abstract.value.Domain): 左辺の値
        RIGHT (abstract.value.Domain): 右辺の値
        operator (str): 演算子
    """
    LEFT: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    RIGHT: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    operator:str = "-"

    @classmethod
    def define_block(cls) -> list[dict]:
        """ブロック定義
        自作ブロックの形状を定義する
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: ブロック定義
        """
        return [{
            "type": "time_delta_arithmetic",
            "tooltip": "日時や秒など、時間を扱う計算をする",
            "message0": "%1 %2 %3",
            "args0": [
                {
                    "type": "input_value",
                    "name": "LEFT",
                    "check": ["Time", "TimeDelta", "Number"]
                },
                {
                    "type": "field_dropdown",
                    "name": "operator",
                    "options": [["+", "+"], ["-", "-"], ["×", "×"], ["÷", "÷"]]
                },
                {
                    "type": "input_value",
                    "name": "RIGHT",
                    "check": ["Time", "TimeDelta", "Number"]
                },
            ],
            "inputsInline": True,
            "output": ["Time", "TimeDelta", "Number"],
            "colour": 310,
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
            "type": "time_delta_arithmetic",
            "fields": {
                "operator": cls.operator
            },
            "inputs": {
                "LEFT": {
                    "shadow": {
                        "type": "_time_now",
                    }
                },
                "RIGHT": {
                    "shadow": {
                        "type": "_time__get",
                    }
                }
            }
        }]
