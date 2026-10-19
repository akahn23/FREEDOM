# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import json

from src import equipment
from src.job.task import abstract
from src.repository import repository


@dataclasses.dataclass
class Domain(abstract.value.Domain):
    """アドレス取得タスク
    Args:
        type (str): ブロック種類
        id (str): ブロックID
        plc (str): PLCノード名
        address (str): アドレス名
    """
    plc: str = "none"
    address: str = json.dumps({ "node": "none", "name": "none" }, ensure_ascii=False)

    @classmethod
    def define_block(cls) -> list[dict]:
        """ブロック定義
        自作ブロックの形状を定義する
        https://developers.google.com/blockly/guides/create-custom-blocks/define/block-definitions?hl=ja
        Returns:
            list[dict]: ブロック定義
        """
        plc_opt:list[list[str, str]] = []
        addr_opt:list[list[str, str]] = []
        for node in repository.retrieve(equipment.plc.Node):
            plc_opt.append([node.domain.name, node.domain.name])
            for address in node.domain.bit_addresses + node.domain.word_addresses:
                addr_opt.append([address.name, json.dumps([node.domain.name, address.name], ensure_ascii=False)])
        return [{
            "type": "equipment.plc.get_address",
            "tooltip": "指定したPLCのアドレス設定を取得する",
            "message0": "PLC %1 アドレス %2",
            "args0": [
                {
                    "type": "field_dropdown",
                    "name": "plc",
                    "options": plc_opt or [["設定なし", "none"]],
                },
                {
                    "type": "field_dropdown",
                    "name": "address",
                    "options": addr_opt or [["設定なし", json.dumps([None, None], ensure_ascii=False)]],
                },
            ],
            "output": "EquipmentPLC",
            "colour": 90,
            "extensions": ["plc_get_address_extension"],
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
            "type": "equipment.plc.get_address"
        }]
