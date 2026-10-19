# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.loop.controls_flow_statements_custom import Domain
from src.job.task.common.loop.exception import LoopBreak, LoopContinue


class Logic(abstract.statement.Logic[Domain]):
    """controls_flow_statements_customタスク ロジック"""
    async def init(self):
        """ジョブ開始時処理"""
        await super().init()

    async def exec(self):
        """タスク実行"""
        if self.domain.FLOW == "BREAK":
            raise LoopBreak()
        if self.domain.FLOW == "CONTINUE":
            raise LoopContinue()
