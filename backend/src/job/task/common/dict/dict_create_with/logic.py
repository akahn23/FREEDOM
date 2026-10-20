# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.dict.dict_create_with import Domain


class Logic(abstract.value.Logic[Domain]):
    """dict_create_with task logic"""
    async def init(self):
        """Called when the job starts"""
        self._key:dict[str, abstract.value.Logic] = dict()
        self._value:dict[str, abstract.value.Logic] = dict()
        for k,v in vars(self.domain).items():
            if isinstance(v, abstract.value.Domain) and k.startswith("KEY"):
                self._key[k] = await v.make_logic(self._job_id, self._logger)
            if isinstance(v, abstract.value.Domain) and k.startswith("VALUE"):
                self._value[k] = await v.make_logic(self._job_id, self._logger)

    async def exec(self) -> dict:
        """Execute the task"""
        keys = sorted(self._key.items(), key=lambda x: int(x[0][3:]))
        ret = dict()
        for key, logic in keys:
            if value := self._value.get("VALUE"+key[3:], None):
                value = await value.exec()
            ret[await logic.exec()] = value
        return ret
