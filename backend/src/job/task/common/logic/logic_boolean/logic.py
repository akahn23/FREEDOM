# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.logic.logic_boolean import Domain


class Logic(abstract.value.Logic[Domain]):
    """logic_boolean task logic"""
    async def exec(self) -> bool:
        """Execute the task"""
        return self.domain.BOOL == "TRUE"
