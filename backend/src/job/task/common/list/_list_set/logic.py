# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.repository import repository
from src import job
from src.job.task import abstract
from src.job.task.common.list._list_set import Domain


class Logic(abstract.statement.Logic[Domain]):
    """list_set task"""
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.VAR["id"]))
        self._VALUE = await self.domain.VALUE.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        self._var.value = await self._VALUE.exec()
