# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.dict.dict_get_item import Domain


class Logic(abstract.value.Logic[Domain]):
    """dict_get_item task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._DICT = await self.domain.DICT.make_logic(self._job_id, self._logger)
        self._KEY = await self.domain.KEY.make_logic(self._job_id, self._logger)

    async def exec(self):
        """Execute the task"""
        _dict:dict = await self._DICT.exec()
        key = await self._KEY.exec()
        if self.domain.MODE == "GET":
            return _dict.get(key)
        elif self.domain.MODE == "GET_REMOVE":
            return _dict.pop(key, None)
