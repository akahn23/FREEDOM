# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src import job, robot
from src.job import command
from src.job.task import abstract
from src.job.task.robot.select import Domain
from src.repository import repository


class Logic(abstract.statement.Logic[Domain]):
    """ロボット選択タスク"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.VAR["id"]))
        if self.domain.condition:
            self._condition = await self.domain.condition.make_logic(self._job_id, self._logger)
        else:
            self._condition = None
        self._result = None

    async def exec(self):
        """タスク実行"""
        self._var.value = None
        try:
            while self._result is None:
                await asyncio.sleep(0)
                name_list = list()
                for node in repository.retrieve(robot.Node):
                    if await self._can_select(node):
                        name_list.append(node.domain.name)
                if name_list:
                    self.domain.command = [command.Button(name, name) for name in name_list]
                else:
                    self.domain.command = [command.Text("選択可能なロボットがありません")]
        finally:
            self.domain.command.clear()
        self._var.value = self._result
        self.domain.command.append(command.Text(f"選択ロボット: {self._var.value}"))

    async def exec_command(self, command:str):
        """コマンド実行
        Args:
            command (str): コマンド内容
        """
        if r := repository.retrieve(robot.Node, name=command):
            if await self._can_select(r[0]):
                node = repository.retrieve(job.active.Node, id=self._job_id)[0]
                r[0].job = node
                self._result = command
            else:
                raise Exception(f"{command} は選択できません")
        else:
            await super().exec_command(command)

    async def _can_select(self, node:robot.Node[robot.Domain]) -> bool:
        """選択可能か
        Args:
            node (robot.Node[robot.Domain]): ロボットノード
        Returns:
            bool: 選択可能
        """
        if node.job:
            return False
        if self._condition:
            try:
                self._var.value = node.domain.name
                return await self._condition.exec()
            finally:
                self._var.value = None
        return True
