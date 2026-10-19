# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job
from src.job.task import abstract
from src.job.task.common.control.controls_warning_clear import Domain
from src.repository import repository


class Logic(abstract.statement.Logic[Domain]):
    """警告リセットタスク処理"""
    async def exec(self):
        """タスク実行"""
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        node.domain.warning_msg.clear()
