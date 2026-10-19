# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job
from src.job import command
from src.job.task import abstract
from src.job.task.common.control.controls_warning import Domain
from src.repository import repository


class Logic(abstract.statement.Logic[Domain]):
    """警告タスク処理"""
    async def init(self):
        """ジョブ開始時処理"""
        await super().init()
        self._warning = await self.domain.warning.make_logic(self._job_id, self._logger)

    async def exec(self):
        """タスク実行"""
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        node.domain.warning_msg.add(await self._warning.exec())
