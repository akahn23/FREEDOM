# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src import abstract, robot, util
from src.infrastructure import Domain


class Node(abstract.Node, abc.ABC):
    def __init__(self):
        """Abstract infrastructure equipment node"""
        self.domain = Domain()

    @abc.abstractmethod
    def fetch_status(self) -> util.status.Status:
        """Get the status
        Returns:
            util.status.Status: Status
        """
        raise NotImplementedError("Subclasses must implement fetch_status method")

    @abc.abstractmethod
    def fetch_command(self) -> list:
        """Get manual operations
        Returns:
            list: Operation contents
        """
        raise NotImplementedError("Subclasses must implement fetch_command method")

    @abc.abstractmethod
    async def accept(self, robot:robot.Node[robot.Domain]) -> bool:
        """Grant infrastructure handshake permission to a robot
        Args:
            robot (robot.Node): Robot node
        """
        raise NotImplementedError("Subclasses must implement accept method")

    @abc.abstractmethod
    async def cancel(self, robot:robot.Node[robot.Domain]) -> bool:
        """End the infrastructure handshake for a robot
        Args:
            robot (robot.Node): Robot node
        """
        raise NotImplementedError("Subclasses must implement cancel method")
