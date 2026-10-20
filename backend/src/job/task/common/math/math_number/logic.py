# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.math.math_number import Domain


class Logic(abstract.value.Logic[Domain]):
    """math_number task logic"""
    async def exec(self) -> int|float:
        """Execute the task"""
        return self.domain.NUM
