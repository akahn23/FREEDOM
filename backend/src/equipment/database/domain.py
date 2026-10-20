# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import inspect

from src import abstract, equipment


@dataclasses.dataclass
class NodeDomain(abstract.Domain):
    """Database node domain
    Attributes:
        enable (bool): Enabled
        name (str): Name
        interface (str): Interface name
        dsn (str): Database connection string
        schema (str): Schema name
        table (str): Table name
        timeout (float): Communication timeout
        update_cycle (float): Update cycle
        location (list[float]): Location
        data (list[dict]): Data
    """
    enable: bool = True
    name: str = ""
    interface: str = "Dummy"
    dsn: str = "database://user:password@host:port/dbname"
    schema: str = "public"
    table: str = ""
    timeout: float = 5.0
    update_cycle: float = 1.0
    location: list[float] = dataclasses.field(default_factory=lambda: [0.0, 0.0])

    def __post_init__(self):
        """Post-initialization processing"""
        self.data:list[dict] = list()

    @classmethod
    def make_form(cls):
        """Create the settings form"""
        return {
            "enable": {
                "type": "switch",
                "label": "有効",
            },
            "name": {
                "type": "text",
                "label": "名前",
            },
            "interface": {
                "type": "select",
                "label": "インターフェース",
                "items": {name: name for name, _ in inspect.getmembers(equipment.database.access, inspect.isclass)},
            },
            "dsn": {
                "type": "text",
                "label": "接続先DSN",
            },
            "schema": {
                "type": "text",
                "label": "スキーマ名",
            },
            "table": {
                "type": "text",
                "label": "テーブル名",
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
            "location": {
                "type": "location",
                "label": "位置",
            }
        }


@dataclasses.dataclass
class Domain(abstract.Domain):
    """Database domain
    Attributes:
        node_domain (list[NodeDomain]): List of node settings
    """
    node_domain:list[NodeDomain] = dataclasses.field(default_factory=list)

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
