# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio

from src.repository import repository
from src import job
from src.abstract import Node
from src.job import command
from src.job.task import abstract
from src.job.task.job.active.exec import Domain


class Logic(abstract.statement.Logic[Domain]):
    """Job execution task logic"""
    async def init(self):
        """Called when the job starts"""
        await super().init()
        self._kwargs = await self.domain.kwargs.make_logic(self._job_id, self._logger)
        node = repository.retrieve(job.active.Node, id=self._job_id)[0]
        self._var = next(node.retrieve_variables(id=self.domain.var["id"]))

    async def exec(self):
        """Execute the task"""
        kwargs:dict|None = await self._kwargs.exec()
        if kwargs is None:
            kwargs = dict()
        for k, v in kwargs.items():
            if isinstance(v, Node):
                kwargs[k] = v.domain.name
        try:
            job_id = await repository.retrieve(job.create.Node)[0].active(self.domain.job, **kwargs)
        except Exception as e:
            self._logger.error(f"Failed to execute job: {type(e)} - {e} job={self.domain.job} {kwargs=}")
            raise Exception(f"{self.domain.job}の実行に失敗")
        child = repository.retrieve(job.active.Node, id=job_id)[0]
        child.domain.visible = False
        parent = repository.retrieve(job.active.Node, id=self._job_id)[0]
        prev_warning_msg = set()
        try:
            while not child._task.done():
                parent.domain.error_msg.update(child.domain.error_msg)
                if child.domain.warning_msg != prev_warning_msg:
                    parent.domain.warning_msg.difference_update(prev_warning_msg)
                    parent.domain.warning_msg.update(child.domain.warning_msg)
                    prev_warning_msg = set(child.domain.warning_msg)
                await asyncio.sleep(0)
            self._var.value = child._task.result()
            if self._var.value is not None:
                self.domain.command.append(command.Text(str(self._var.value)))
                self._logger.info(f"return={self._var.value}")
        finally:
            child._task.cancel()
            if child.domain.warning_msg != prev_warning_msg:
                parent.domain.warning_msg.difference_update(prev_warning_msg)
                parent.domain.warning_msg.update(child.domain.warning_msg)
                prev_warning_msg = set(child.domain.warning_msg)
