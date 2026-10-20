# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import random

from src.job.task import abstract
from src.job.task.common.math.math_random_float import Domain


class Logic(abstract.value.Logic[Domain]):
    """math_random_float task logic"""

    async def exec(self) -> float:
        """Execute the task"""
        return random.random()
