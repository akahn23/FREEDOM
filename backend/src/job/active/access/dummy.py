# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from datetime import datetime
import uuid

from src import freedom
from src.repository import repository
from src.job.active import Interface, Domain, NodeDomain


class Dummy(Interface):
    def __init__(self, domain:Domain):
        """Active job dummy database connection
        Args:
            domain (Domain): Domain
        """
        self._database:list[NodeDomain] = getattr(
            repository.retrieve(freedom.main.Node)[0].domain.conf,
            "job_active",
            list()
        )

    async def insert(self, name:str, task:dict, variables:list[dict]) -> dict:
        """Save an active job
        Args:
            name (str): Job name
            task (dict): Task contents
            variables (list[dict]): Task variables
        Returns:
            dict: Active job settings
        """
        domain = NodeDomain(uuid.uuid4(), datetime.now(), name, task, variables)
        self._database.append(domain)
        return dataclasses.asdict(domain)

    async def fetch(self) -> list[dict]:
        """Get active jobs
        Returns:
            list[dict]: Active job settings
        """
        return [dataclasses.asdict(domain) for domain in self._database]

    async def update(self, node_list:list[NodeDomain]):
        """Update an active job
        Args:
            node_list (list[NodeDomain]): List of active jobs
        """
        self._database = node_list
