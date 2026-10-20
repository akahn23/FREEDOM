# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import copy

from src import freedom
from src.repository import repository
from src.job.create import Interface, Domain, Column


class Dummy(Interface):
    def __init__(self, domain:Domain):
        """Job creation dummy database connection
        Args:
            domain (Domain): Domain
        """
        self._database:list[Column] = getattr(
            repository.retrieve(freedom.main.Node)[0].domain.conf,
            "job_create",
            list()
        )

    async def fetch_name_list(self, user_id:str|None=None, is_admin:bool=False) -> list[str]:
        """Get the list of job names
        Args:
            user_id (str|None): User ID
            is_admin (bool): Admin flag (True fetches all)
        Returns:
            list[str]: List of job names
        """
        return [row.name for row in self._database]

    async def fetch_workspace(self, name:str) -> dict:
        """Get the Blockly workspace
        Args:
            name (str): Job name
        Returns:
            dict: Blockly workspace
        """
        return copy.deepcopy(next(row.workspace for row in self._database if row.name == name))

    async def update(self, name:str, workspace:dict):
        """Update a job
        Args:
            name (str): Job name
            workspace (dict): Blockly workspace
        """
        for row in self._database:
            if row.name == name:
                row.workspace = workspace
                return
        self._database.append(Column(name, workspace))

    async def delete(self, name:str):
        """Delete a job
        Args:
            name (str): Job name
        """
        self._database = [row for row in self._database if row.name != name]
