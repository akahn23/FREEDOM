# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import abstract, util


@dataclasses.dataclass
class NodeDomain(abstract.Domain):
    """IoTDataShare equipment node settings
    Args:
        enable (bool): Enabled
        name (str): Name
        ip (str): IP address
        port (int): Port number
        timeout (float): Communication timeout
        update_cycle (float): Update cycle
    Note:
        status (util.enum.Status): Status
        connect_list (set[str]): List of IoTDataShare controllers already connected
    """
    enable:bool = True
    name:str = ""
    ip:str = "0.0.0.0"
    port:int = 80
    timeout:float = 1.0
    update_cycle:float = 1.0

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return {
            "enable": {
                "type": "switch",
                "label": "有効",
            },
            "name": {
                "type": "text",
                "label": "名前",
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
        }

    def __post_init__(self):
        """Post-initialization processing"""
        self.status = util.status.State.HIDE
        self.connect_list = list()


@dataclasses.dataclass
class Domain(abstract.Domain):
    """IoTDataShare settings
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
                "unique": ["name"]
            }
        }

    def __post_init__(self):
        """Post-initialization processing"""
        self.node_domain = [NodeDomain(**node_domain) for node_domain in self.node_domain if node_domain.get("enable", False)]
