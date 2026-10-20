# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import abstract, job


@dataclasses.dataclass
class Column:
    """Column definition
    Args:
        name (str): Job name
        workspace (dict): Blockly workspace
    """
    name:str
    workspace:dict


@dataclasses.dataclass
class Domain(abstract.database.Domain):
    """Job creation settings
    Args:
        interface (str): Interface name
        dsn (str): Database connection string
        schema (str): Schema name
        table (str): Table name
        update_cycle (float): Update cycle
    """
    table:str = "job_create"

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return super().make_form(job.create.access)

    def __post_init__(self):
        """Post-initialization processing"""
        super().__post_init__(job.create.access)
