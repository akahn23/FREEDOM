# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

from src.job.task import abstract
from src.job.task.common.time._time_now import Domain


class Logic(abstract.value.Logic[Domain]):
    """Current time get task logic"""
    async def exec(self) -> datetime:
        """Execute the task"""
        return datetime.now()
