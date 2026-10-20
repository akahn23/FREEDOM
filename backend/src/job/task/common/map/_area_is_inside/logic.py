# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import util
from src.job.task import abstract
from src.job.task.common.map._area_is_inside import Domain


class Logic(abstract.value.Logic[Domain]):
    """Inside-area check task logic"""
    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        self._location = await self.domain.location.make_logic(self._job_id, self._logger)
        self._area_list = await self.domain.area_list.make_logic(self._job_id, self._logger)

    async def exec(self) -> bool:
        """Execute the task"""
        location:list[float] = await self._location.exec()
        area_list:list[util.map.Area] = await self._area_list.exec()
        return util.map._is_inside(location, area_list)
