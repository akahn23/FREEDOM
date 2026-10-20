# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src.job.task import abstract


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """時間差分取得タスク
    Args:
        type (str): ブロック種類
        id (str): ブロックID
        time (abstract.value.Domain): 入力された数値
        unit (str): 時間の単位
    """
    time: abstract.value.Domain = dataclasses.field(default_factory=abstract.value.Domain)
    unit:str = "seconds"

    @classmethod
    def define_block(cls) -> list[dict]:
        """ブロック定義
        自作ブロックの形状を定義する
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: ブロック定義
        """
        return [{
            "type": "time_delta_duration",
            "tooltip": "時間の差分を取得する",
            "message0": "%1 %2 ",
            "args0": [
                {
                    "type": "input_value",
                    "name": "time",
                    "check": "Number"
                },
                {
                    "type": "field_dropdown",
                    "name": "unit",
                    "options": [["秒", "seconds"], ["分", "minutes"], ["時間", "hours"]]
                }
            ],
            "output": "TimeDelta",
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
            "type": "time_delta_duration",
            "inputs": {
                "time": {
                    "shadow": {
                        "type": "math_number",
                        "fields": {
                            "NUM": 1
                        }
                    }
                }
            }
        }]
