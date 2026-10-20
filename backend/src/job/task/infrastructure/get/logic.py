# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import infrastructure
from src.repository import repository
from src.job.task import abstract
from src.job.task.infrastructure.get import Domain


class Logic(abstract.value.Logic[Domain]):
    """Infrastructure equipment get task logic"""
    async def init(self):
        """Called when the job starts or resumes"""
        if node := repository.retrieve(infrastructure.Node, name=self.domain.name):
            self._node = node[0]
        else:
            raise(f"Infrastructure {self.domain.name} does not exist")

    async def exec(self) -> infrastructure.Node:
        """Execute the task"""
        return self._node
