# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

from src import job
from src.job import command
from src.job.task import abstract
from src.job.task.common.loop.controls_for_custom import Domain
from src.job.task.common.loop.exception import LoopBreak, LoopContinue
from src.repository import repository


class Logic(abstract.statement.Logic[Domain]):
    """controls_for_customタスク ロジック"""
    async def init(self):
        """ジョブ開始時処理"""
        await super().init()
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.VAR["id"]))
        if not self.domain.command:
            self._var.value = None
        self._FROM = await self.domain.FROM.make_logic(self._job_id, self._logger)
        self._TO = await self.domain.TO.make_logic(self._job_id, self._logger)
        self._BY = await self.domain.BY.make_logic(self._job_id, self._logger)
        if not self.domain.command:
            self.domain.command.append(command.Text(""))
            if self.domain.DO:
                self.domain.command.append(command.Task(self.domain.DO.id))
        logger = self._logger if self.domain.should_log else logging.getLogger("loop")
        self._DO = await self.domain.DO.make_logic(self._job_id, logger) if self.domain.DO else None

    async def exec(self):
        """タスク実行"""
        logger = self._logger if self.domain.should_log else logging.getLogger("loop")
        start = await self._FROM.exec() if self._var.value is None else self._var.value
        to = await self._TO.exec()
        step = abs(await self._BY.exec())
        if start > to:
            end = to - 1
            step = -step
        else:
            end = to + 1
        for self._var.value in range(start, end, step):
            text:command.Text = self.domain.command[0]
            text.label = f"現在値：{self._var.value} / 終了値：{to}"
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
            await asyncio.sleep(0)
        self.domain.command.clear()
