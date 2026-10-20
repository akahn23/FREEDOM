# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job
from src.repository import repository
from src.job.task import abstract
from src.job.task.infrastructure.is_accepted import Domain


class Logic(abstract.value.Logic[Domain]):
    """Infrastructure equipment passage-permission check task logic"""
    async def exec(self) -> bool:
        """Execute the task"""
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        return await node.accept_infrastructure()
