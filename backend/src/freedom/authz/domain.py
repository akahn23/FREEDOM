# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import abstract, freedom


@dataclasses.dataclass
class Domain(abstract.database.Domain):
    """AuthZ (authorization) settings
    Args:
        interface (str): Interface name
        dsn (str): Database connection DSN
        schema (str): Schema name
        table (str): Table name
        update_cycle (float): Update cycle
    """
    schema: str = "authz"
    table: str = "casbin_rule"

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return super().make_form(freedom.authz.access)

    def __post_init__(self):
        """Post-initialization processing"""
        super().__post_init__(freedom.authz.access)
