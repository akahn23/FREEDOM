# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src.job.create import Domain


class Interface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, domain:Domain):
        """Job creation database connection interface
        Args:
            domain (Domain): Domain
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def fetch_name_list(self, user_id:str|None=None, is_admin:bool=False) -> list[str]:
        """Get the list of job names
        Args:
            user_id (str|None): User ID
            is_admin (bool): Admin flag (True fetches all)
        Returns:
            list[str]: List of job names
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def fetch_workspace(self, name:str) -> dict:
        """Get the Blockly workspace
        Args:
            name (str): Job name
        Returns:
            dict: Blockly workspace
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def update(self, name:str, workspace:dict):
        """Update a job
        Args:
            name (str): Job name
            workspace (dict): Blockly workspace
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def delete(self, name:str):
        """Delete a job
        Args:
            name (str): Job name
        """
        raise NotImplementedError()
