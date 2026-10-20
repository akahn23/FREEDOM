# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import dataclasses
import inspect
import types

from src import abstract, freedom
from src.repository import repository


@dataclasses.dataclass
class Domain(abstract.Domain):
    """Abstract database settings
    Args:
        interface (str): Interface name
        dsn (str): Database connection string
        schema (str): Schema name
        table (str): Table name
        update_cycle (float): Update cycle
    """
    interface:str = ""
    dsn:str = ""
    schema:str = ""
    table:str = ""
    update_cycle:float = 10.0

    @classmethod
    @abc.abstractmethod
    def make_form(cls, access:types.ModuleType):
        """Create the settings form
        Args:
            access (types.ModuleType): Access layer module
        Returns:
            dict: Settings form
        """
        return {
            "interface": {
                "type": "select",
                "label": "インターフェース",
                "items": {name: name for name, _ in inspect.getmembers(access, inspect.isclass)},
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
            "update_cycle": {
                "type": "number",
                "label": "更新周期",
                "suffix": "秒",
                "min": 0,
            }
        }

    @abc.abstractmethod
    def __post_init__(self, access:types.ModuleType):
        """Post-initialization processing
        On the first database build, the freedom.main database settings are used
        Args:
            access (types.ModuleType): Access layer module
        """
        if not self.interface and repository.retrieve(freedom.main.Node):
            main_domain = repository.retrieve(freedom.main.Node)[0].domain
            if hasattr(access, main_domain.interface):
                self.interface = main_domain.interface
                self.dsn = main_domain.dsn
                self.schema = main_domain.schema
            else:
                self.interface = "Dummy"
