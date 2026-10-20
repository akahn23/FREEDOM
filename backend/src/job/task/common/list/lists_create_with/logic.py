# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.list.lists_create_with import Domain


class Logic(abstract.value.Logic[Domain]):
    """lists_create_withタスク処理"""
    async def init(self):
        """ジョブ開始時処理"""
        await super().init()
        self._add:dict[str, abstract.value.Logic] = dict()
        for k,v in vars(self.domain).items():
            if isinstance(v, abstract.value.Domain) and k.startswith("ADD"):
                self._add[k] = await v.make_logic(self._job_id, self._logger)

    async def exec(self) -> list:
        """タスク実行"""
        add = sorted(self._add.items(), key=lambda x: int(x[0][3:]))
        ret = list()
        for key, logic in add:
            for _ in range(len(ret), int(key[3:])):
                ret.append(None)
            ret.append(await logic.exec())
        return ret
