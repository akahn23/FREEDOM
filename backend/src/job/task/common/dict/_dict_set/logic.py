# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job
from src.job.task import abstract
from src.job.task.common.dict._dict_set import Domain
from src.repository import repository


class Logic(abstract.statement.Logic[Domain]):
    """dict_setタスク"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.VAR["id"]))
        self._VALUE = await self.domain.VALUE.make_logic(self._job_id, self._logger)

    async def exec(self):
        """タスク実行"""
        self._var.value = await self._VALUE.exec()
