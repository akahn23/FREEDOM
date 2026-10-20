# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.list.lists_setIndex_custom import Domain


class Logic(abstract.statement.Logic[Domain]):
    """lists_setIndex_custom task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._LIST = await self.domain.LIST.make_logic(self._job_id, self._logger)
        self._AT = await self.domain.AT.make_logic(self._job_id, self._logger)
        self._TO = await self.domain.TO.make_logic(self._job_id, self._logger)

    async def exec(self) -> list:
        """Execute the task"""
        LIST:list = await self._LIST.exec()
        AT = int(await self._AT.exec())
        TO = await self._TO.exec()
        if self.domain.WHERE == "FROM_START":
            index = AT - 1
        elif self.domain.WHERE == "FROM_END":
            index = -AT
        else:
            raise ValueError(f"Unknown where: {self.domain.WHERE}")
        if self.domain.MODE == "SET":
            LIST[index] = TO
        elif self.domain.MODE == "INSERT":
            LIST.insert(index, TO)
        else:
            raise ValueError(f"Unknown mode: {self.domain.MODE}")
