# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from datetime import datetime

from src import abstract, freedom


@dataclasses.dataclass
class Column:
    """Log column definition
    Args:
        time (datetime): When the log was emitted
        name (str): Logger name
        levelname (str): Log level name
        message (str): Log message
    """
    time:datetime
    name:str
    levelname:str
    message:str


@dataclasses.dataclass
class Domain(abstract.database.Domain):
    """Log settings
    Args:
        interface (str): Interface name
        dsn (str): Database connection string
        schema (str): Schema name
        table (str): Table name
        update_cycle (float): Update cycle
        retention_period (int): Retention period (days)
    """
    table:str = "freedom_log"
    retention_period:int = 90

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return super().make_form(freedom.log.access) | {
            "retention_period": {
                "type": "number",
                "label": "保存期間",
                "suffix": "日",
                "integer": True,
                "min": 1,
            }
        }

    def __post_init__(self):
        """Post-initialization processing"""
        super().__post_init__(freedom.log.access)
