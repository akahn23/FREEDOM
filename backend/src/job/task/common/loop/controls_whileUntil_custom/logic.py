# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

from src.job import command
from src.job.task import abstract
from src.job.task.common.loop.controls_whileUntil_custom import Domain
from src.job.task.common.loop.exception import LoopBreak, LoopContinue


class Logic(abstract.statement.Logic[Domain]):
    """controls_whileUntil_customタスク処理"""
    async def init(self):
        """ジョブ開始時処理"""
        await super().init()
        self._BOOL = await self.domain.BOOL.make_logic(self._job_id, self._logger)
        logger = self._logger if self.domain.should_log else logging.getLogger("loop")
        self._DO = await self.domain.DO.make_logic(self._job_id, logger) if self.domain.DO else None
        if not self.domain.command and self.domain.DO:
            self.domain.command.append(command.Task(self.domain.DO.id))

    async def exec(self):
        """タスク実行"""
        logger = self._logger if self.domain.should_log else logging.getLogger("loop")
        while True:
            if self.domain.condition is None:
                self.domain.condition = await self._BOOL.exec()
                if self.domain.MODE == "WHILE" and not self.domain.condition:
                    break
                elif self.domain.MODE == "UNTIL" and self.domain.condition:
                    break
            try:
                if self.domain.DO:
                    task:command.Task = self.domain.command[0]
                    await task.exec(self._DO, logger)
            except LoopBreak:
                break
            except LoopContinue:
                pass
            self.domain.DO = abstract.statement.Domain.to_domain(self.domain.DO_copy) if self.domain.DO_copy else None
            self._DO = await self.domain.DO.make_logic(self._job_id, logger) if self.domain.DO else None
            self.domain.condition = None
            await asyncio.sleep(0)
        self.domain.command.clear()
