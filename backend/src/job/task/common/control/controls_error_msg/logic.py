# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job
from src.repository import repository
from src.job.task import abstract
from src.job.task.common.control.controls_error_msg import Domain


class Logic(abstract.value.Logic[Domain]):
    """Get-error-contents task logic"""
    async def exec(self):
        """Execute the task"""
        j = repository.retrieve(job.active.Node, id=self._job_id)[0]
        return ", ".join(j.domain.error_msg)
