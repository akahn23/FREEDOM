# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job, util
from src.job.task import abstract
from src.job.task.common.map._area__get import Domain
from src.repository import repository


class Logic(abstract.value.Logic[Domain]):
    """エリア変数取得タスク処理"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.VAR["id"]))

    async def exec(self) -> list[util.map.Area]:
        """タスク実行"""
        return self._var.value
