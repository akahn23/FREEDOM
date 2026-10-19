# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
from datetime import datetime, timedelta

from src import infrastructure, job, robot, util
from src.job import command
from src.job.task import abstract
from src.job.task.infrastructure.accept import Domain
from src.repository import repository


class Logic(abstract.statement.Logic[Domain]):
    """インフラ設備連携タスク処理"""
    async def init(self):
        """ジョブ開始時処理"""
        await super().init()
        self._robot = await self.domain.robot.make_logic(self._job_id, self._logger)
        self._exclude = await self.domain.exclude.make_logic(self._job_id, self._logger) if self.domain.exclude else None
        self._update_cycle = await self.domain.update_cycle.make_logic(self._job_id, self._logger)
        self._warning_time = await self.domain.warning_time.make_logic(self._job_id, self._logger)
        self._task = await self.domain.task.make_logic(self._job_id, self._logger) if self.domain.task else None
        if not self.domain.command and self.domain.task:
            self.domain.command.append(command.Task(self.domain.task.id))
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        for node in repository.retrieve(infrastructure.Node):
            status:util.status.Status = node.fetch_status()
            if status.state == util.status.State.ERROR:
                raise Exception(f"インフラ設備異常 {node.domain.name}:{status.info}")
        self._is_accepted = None

    async def exec(self):
        """タスク実行"""
        loop_task = asyncio.create_task(self._loop())
        try:
            sub_task:command.Task = self.domain.command[0]
            await sub_task.exec(self._task, self._logger)
        finally:
            loop_task.cancel()
            self._is_accepted = None
        for node in await self._fetch_infrastructure_node():
            await node.cancel(await self._robot.exec())

    async def exec_command(self, command:str) -> bool|None:
        """コマンド実行
        Args:
            command (str): コマンド内容
        Returns:
            bool|None: 実行結果
        """
        if command == "accept_infrastructure":
            is_accepted = getattr(self, "_is_accepted", None) and self._is_accepted
            if is_accepted:
                return await self._accept_infrastructure()
            return is_accepted
        else:
            await super().exec_command(command)

    async def _loop(self):
        """インフラ連携ループ"""
        update_cycle:timedelta = await self._update_cycle.exec()
        while True:
            warning_time:timedelta = await self._warning_time.exec()
            is_accepted = await self._accept_infrastructure()
            if not is_accepted and self._is_accepted != is_accepted:
                time = datetime.now()
            if not is_accepted and datetime.now() - time > warning_time:
                node = repository.retrieve(job.active.Node, id=self._job_id)[0]
                node.domain.warning_msg.add("インフラ許可待ち超過警告")
            else:
                node = repository.retrieve(job.active.Node, id=self._job_id)[0]
                node.domain.warning_msg.discard("インフラ許可待ち超過警告")
            self._is_accepted = is_accepted
            await asyncio.sleep(update_cycle.total_seconds())

    async def _accept_infrastructure(self) -> bool:
        """インフラ連携
        Returns:
            bool: 連携結果
        """
        async def _accept(i:infrastructure.Node, r:robot.Node) -> bool:
            """連携タスク
            同じ優先度のインフラを同時に連携するため、連携部分のメソッドを抜き出し
            Args:
                i (infrastructure.Node): インフラノード
                r (robot.Node): ロボットノード
            Returns:
                bool: 連携結果
            """
            try:
                return await i.accept(r)
            except Exception as e:
                self._logger.error(f"インフラ連携失敗: {i.domain.name} {type(e)}-{e}")
                j = repository.retrieve(job.active.Node, id=self._job_id)[0]
                j.domain.error_msg.add(f"インフラ連携失敗: {i.domain.name}")
                return False
        group:dict[int,list[infrastructure.Node]] = dict()
        for node in await self._fetch_infrastructure_node():
            if node.domain.priority not in group.keys():
                group[node.domain.priority] = list()
            group[node.domain.priority].append(node)
        r = await self._robot.exec()
        for _, node_list in sorted(group.items(), key=lambda x:x[0], reverse=True):
            if not all(await asyncio.gather(*(_accept(node, r) for node in node_list))):
                return False
        return True

    async def _fetch_infrastructure_node(self) -> set[infrastructure.Node]:
        """連携インフラ取得
        Returns:
            set[infrastructure.Node]: 連携インフラノード
        """
        exclude:list[infrastructure.Node] = await self._exclude.exec() if self._exclude else list()
        if type(exclude) is not list:
            exclude = [exclude]
        return set(repository.retrieve(infrastructure.Node)).difference(exclude)
