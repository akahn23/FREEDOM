# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import robot
from src.job.task import abstract
from src.job.task.robot.dummy.place import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Dummy placement task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._robot = await self.domain.robot.make_logic(self._job_id, self._logger)
        self._location = await self.domain.location.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        dummy:robot.dummy.Node = await self._robot.exec()
        location:list[float] = await self._location.exec()
        lat, lon = location
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"Invalid coordinates: ({lat}, {lon})")
        dummy.domain.location = [lat, lon]
