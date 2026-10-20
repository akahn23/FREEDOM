# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job, util
from src.repository import repository
from src.job.task import abstract
from src.job.task.common.map._area__get import Domain


class Logic(abstract.value.Logic[Domain]):
    """Area variable get task logic"""
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.VAR["id"]))

    async def exec(self) -> list[util.map.Area]:
        """Execute the task"""
        return self._var.value
