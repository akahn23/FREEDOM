# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job
from src.job.task import abstract
from src.job.task.common.control.controls_error_msg import Domain
from src.repository import repository


class Logic(abstract.value.Logic[Domain]):
    """異常内容取得タスク処理"""
    async def exec(self):
        """タスク実行"""
        j = repository.retrieve(job.active.Node, id=self._job_id)[0]
        return ", ".join(j.domain.error_msg)
