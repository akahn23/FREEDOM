# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.list.lists_create_with import Domain


class Logic(abstract.value.Logic[Domain]):
    """lists_create_with task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        for k,v in vars(self.domain).items():
            if isinstance(v, abstract.value.Domain):
                setattr(self, k, await v.make_logic(self._job_id, self._logger))

    async def exec(self) -> list:
        """Execute the task"""
        add: list = list()
        for name, logic in vars(self).items():
            if name.startswith("ADD") and isinstance(logic, abstract.value.Logic):
                add.append(name)
        add.sort(key=lambda x:int(x[3:]))
        return [await getattr(self, name).exec() for name in add]

    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._add:dict[str, abstract.value.Logic] = dict()
        for k,v in vars(self.domain).items():
            if isinstance(v, abstract.value.Domain) and k.startswith("ADD"):
                self._add[k] = await v.make_logic(self._job_id, self._logger)

    async def exec(self) -> list:
        """Execute the task"""
        add = sorted(self._add.items(), key=lambda x: int(x[0][3:]))
        ret = list()
        for key, logic in add:
            for _ in range(len(ret), int(key[3:])):
                ret.append(None)
            ret.append(await logic.exec())
        return ret
