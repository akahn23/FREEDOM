# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src.job.active import Domain


class Interface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, domain:Domain):
        """Active job database connection interface
        Args:
            domain (Domain): Domain
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def insert(self, name:str, task:dict, variables:list[dict]) -> dict:
        """Save an active job
        Args:
            name (str): Job name
            task (dict): Task contents
            variables (list[dict]): Task variables
        Returns:
            dict: Active job settings
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def fetch(self) -> list[dict]:
        """Get active jobs
        Returns:
            list[dict]: Active job settings
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def update(self, node_list:list[dict]):
        """Update an active job
        Args:
            node_list (list[dict]): List of active job settings
        """
        raise NotImplementedError()
