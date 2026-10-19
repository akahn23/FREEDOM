# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job
from src.job.task import abstract
from src.job.task.infrastructure.is_accepted import Domain
from src.repository import repository


class Logic(abstract.value.Logic[Domain]):
    """インフラ設備通行許可判定タスク処理"""
    async def exec(self) -> bool:
        """タスク実行"""
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        return await node.accept_infrastructure()
