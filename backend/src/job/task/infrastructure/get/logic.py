# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import infrastructure
from src.job.task import abstract
from src.job.task.infrastructure.get import Domain
from src.repository import repository


class Logic(abstract.value.Logic[Domain]):
    """インフラ設備取得タスク処理"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        if node := repository.retrieve(infrastructure.Node, name=self.domain.name):
            self._node = node[0]
        else:
            raise(f"Infrastructure {self.domain.name} does not exist")

    async def exec(self) -> infrastructure.Node:
        """タスク実行"""
        return self._node
