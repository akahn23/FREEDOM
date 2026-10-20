# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job
from src.repository import repository
from src.job.task import abstract
from src.job.task.common.control.controls_warning_clear import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Warning reset task logic"""
    async def exec(self):
        """Execute the task"""
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        node.domain.warning_msg.clear()
