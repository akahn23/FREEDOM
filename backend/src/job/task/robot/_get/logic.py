# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import job, robot
from src.job.task import abstract
from src.job.task.robot._get import Domain
from src.repository import repository


class Logic(abstract.value.Logic[Domain]):
    """ロボット変数取得タスク処理"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.VAR["id"]))

    async def exec(self) -> robot.Node:
        """タスク実行"""
        if self._var.value is None:
            return None
        if ret := repository.retrieve(robot.Node, name=self._var.value):
            return ret[0]
        raise Exception(f"Robot {self._var.value} does not exist")
