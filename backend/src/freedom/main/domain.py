# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing

if typing.TYPE_CHECKING:
    import config.dummy


@dataclasses.dataclass
class Domain:
    """FREEDOM settings
    Args:
        interface (str): Interface name
        dsn (str): Database connection string
        schema (str): Schema name
        table (str): Table name
        update_cycle (float): Update cycle
    Note:
        conf (config.dummy): Initial settings
    """
    interface:str
    dsn:str
    schema:str
    table:str
    update_cycle:float

    @classmethod
    def make_form(cls):
        """Create the settings form
        Not created here; see freedom.user_interface.logic.freedom.main.Config
        """
        pass

    def __post_init__(self):
        """Post-initialization processing"""
        self.conf:config.dummy = None
