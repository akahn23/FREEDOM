# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src.repository import repository
from src import job
from src.abstract import Node
from src.job import command
from src.job.task import abstract
from src.job.task.common.control.controls_select import Domain


class Logic(abstract.statement.Logic[Domain]):
    """ボタン選択タスク処理"""
    async def init(self):
        """ジョブ開始時処理"""
        await super().init()
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.var["id"]))
        self._map_logic = await self.domain.map.make_logic(self._job_id, self._logger) if self.domain.map else None
        self._map = dict()

    async def exec(self):
        """タスク実行"""
        self.domain.command.clear()
        try:
            self._map:dict = await self._map_logic.exec() if self._map_logic else dict()
            self._var.value = None
            for label, value in self._map.items():
                if isinstance(value, Node):
                    value = value.domain.name
                self.domain.command.append(command.Button(label, label))
            while self._var.value is None:
                await asyncio.sleep(0)
        except BaseException:
            self.domain.command.clear()
        finally:
            self._map.clear()

    async def exec_command(self, cmd:str):
        """コマンド実行
        Args:
            cmd (str): コマンド内容
        """
        if cmd in self._map:
            self._logger.info(f"controls_select: selected {cmd}")
            self._var.value = self._map[cmd]
            self.domain.command.clear()
            self.domain.command.append(command.Text(cmd))
        else:
            await super().exec_command(cmd)
