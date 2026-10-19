# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

from src import job
from src.job.task import abstract
from src.job.task.common.time._time__get import Domain
from src.repository import repository


class Logic(abstract.value.Logic[Domain]):
    """時刻変数取得タスク ロジック"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.VAR["id"]))

    async def exec(self) -> datetime|None:
        """タスク実行"""
        return self._var.value
