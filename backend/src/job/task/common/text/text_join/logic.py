# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.text.text_join import Domain


class Logic(abstract.value.Logic[Domain]):
    """text_join task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._add:dict[str, abstract.value.Logic] = dict()
        for k,v in vars(self.domain).items():
            if isinstance(v, abstract.value.Domain) and k.startswith("ADD"):
                self._add[k] = await v.make_logic(self._job_id, self._logger)

    async def exec(self) -> str:
        """Execute the task"""
        add = sorted(self._add.items(), key=lambda x: int(x[0][3:]))
        return "".join([str(await logic.exec()) for _, logic in add])
