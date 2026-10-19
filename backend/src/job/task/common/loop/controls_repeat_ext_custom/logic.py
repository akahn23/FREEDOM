# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

from src.job import command
from src.job.task import abstract
from src.job.task.common.loop.controls_repeat_ext_custom import Domain
from src.job.task.common.loop.exception import LoopBreak, LoopContinue


class Logic(abstract.statement.Logic[Domain]):
    """controls_repeat_ext_customタスク ロジック"""
    async def init(self):
        """ジョブ開始時処理"""
        await super().init()
        if not self.domain.command:
            self.domain.count = 0
        self._TIMES = await self.domain.TIMES.make_logic(self._job_id, self._logger)
        if not self.domain.command:
            self.domain.command.append(command.Text(""))
            if self.domain.DO:
                self.domain.command.append(command.Task(self.domain.DO.id))
        logger = self._logger if self.domain.should_log else logging.getLogger("loop")
        self._DO = await self.domain.DO.make_logic(self._job_id, logger) if self.domain.DO else None

    async def exec(self):
        """タスク実行"""
        times = await self._TIMES.exec()
        logger = self._logger if self.domain.should_log else logging.getLogger("loop")
        while self.domain.count < times:
            text:command.Text = self.domain.command[0]
            text.label = f"{self.domain.count+1} / {times}周目"
            try:
                if self.domain.DO:
                    task:command.Task = self.domain.command[1]
                    await task.exec(self._DO, logger)
            except LoopBreak:
                break
            except LoopContinue:
                pass
            self.domain.DO = abstract.statement.Domain.to_domain(self.domain.DO_copy) if self.domain.DO_copy else None
            self._DO = await self.domain.DO.make_logic(self._job_id, logger) if self.domain.DO else None
            self.domain.count += 1
            await asyncio.sleep(0)
        self.domain.command.clear()
