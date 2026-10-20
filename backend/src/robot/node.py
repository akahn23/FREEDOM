# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src import abstract, job, util
from src.repository import repository
from src.robot import Domain


class Node[D:Domain](abstract.Node, abc.ABC):
    def __init__(self, domain:D):
        """Abstract robot node"""
        self.domain = domain
        self.job:job.active.Node = None

    async def _update(self):
        """Update the status
        Update self.job
        """
        for node in repository.retrieve(job.active.Node):
            if next(node.retrieve_variables(type="Robot", value=self.domain.name), None):
                self.job = node
                return
        self.job = None

    @abc.abstractmethod
    def fetch_status(self) -> util.status.Status:
        """Get the status
        Returns:
            util.status.Status: Status
        """
        raise NotImplementedError("Subclasses must implement fetch_status method")
