# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import inspect

from src import abstract, infrastructure, util


@dataclasses.dataclass
class NodeDomain(infrastructure.Domain):
    """Shutter equipment node settings
    Args:
        enable (bool): Enabled
        name (str): Name
        location (list[float]): Location
        priority (int): Priority
        interface (str): Interface
        ip (str): IP address
        port (int): Port number
        read_address (int): Address to read
        open_state (bool): Address state when fully open
        write_address (int): Address to write
        timeout (float): Communication timeout
        update_cycle (float): Update cycle
        area_list (list[util.map.Area]): Linked areas
    """
    interface:str = "Dummy"
    ip:str = "0.0.0.0"
    port:int = 80
    read_address:int = 0
    open_state:bool = False
    write_address:int = 0
    timeout:float = 1.0
    update_cycle:float = 1.0
    area_list:list[util.map.Area] = dataclasses.field(default_factory=list)

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return super().make_form() | {
            "interface": {
                "type": "select",
                "label": "インターフェース",
                "items": {name: name for name, _ in inspect.getmembers(infrastructure.shutter.access, inspect.isclass)},
            },
            "ip": {
                "type": "text",
                "label": "IPアドレス",
            },
            "port": {
                "type": "number",
                "label": "ポート番号",
                "integer": True,
                "min": 0,
            },
            "read_address": {
                "type": "number",
                "label": "読込みアドレス",
                "integer": True,
                "min": 0,
            },
            "open_state": {
                "type": "radio",
                "label": "開き端時の読込みアドレス状態",
                "items": {"0": False, "1": True},
            },
            "write_address": {
                "type": "number",
                "label": "書込みアドレス",
                "integer": True,
                "min": 0,
            },
            "timeout": {
                "type": "number",
                "label": "通信タイムアウト",
                "suffix": "秒",
                "min": 0,
            },
            "update_cycle": {
                "type": "number",
                "label": "更新周期",
                "suffix": "秒",
                "min": 0,
            },
            "area_list": {
                "type": "area",
                "label": "連携エリア",
            },
        }

    def __post_init__(self):
        """Post-initialization processing"""
        super().__post_init__()
        self.area_list = [util.map.Area(**area) if isinstance(area, dict) else area for area in self.area_list]


@dataclasses.dataclass
class Domain(abstract.Domain):
    """Shutter equipment settings
    Args:
        node_domain (list[NodeDomain]): List of node settings
    """
    node_domain:list[NodeDomain] = dataclasses.field(default_factory=lambda:list())

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return {
            "node_domain": {
                "type": "node",
                "label": "ノード設定",
                "default": dataclasses.asdict(NodeDomain()),
                "forms": NodeDomain.make_form(),
                "unique": ["name"],
            }
        }

    def __post_init__(self):
        """Post-initialization processing"""
        self.node_domain = [NodeDomain(**node_domain) for node_domain in self.node_domain if node_domain.get("enable", False)]
