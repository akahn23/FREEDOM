# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import logging
import typing

if typing.TYPE_CHECKING:
    from src.job.task.abstract.value import Domain


class Logic[D:Domain](abc.ABC):
    def __init__(self, domain:D, job_id:int, logger:logging.Logger):
        """Abstract value task logic
        Args:
            domain (D): Settings
            job_id (int): Job ID
            logger (logging.Logger): Logger
        """
        self.domain = domain
        self._job_id = job_id
        self._logger = logger

    async def init(self):
        """Called when the job starts or resumes"""
        pass

    @abc.abstractmethod
    async def exec(self):
        """Execute the task"""
        raise NotImplementedError("Subclasses must implement exec method")
