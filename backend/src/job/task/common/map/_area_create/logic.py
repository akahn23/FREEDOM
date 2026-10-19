# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import util
from src.job.task import abstract
from src.job.task.common.map._area_create import Domain


class Logic(abstract.value.Logic[Domain]):
    """エリア設定タスク処理"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()

    async def exec(self) -> list[util.map.Area]:
        """タスク実行"""
        if self.domain.area_list is None:
            return[]
        return [util.map.Area(name=area["name"], vertex_list=area["vertex_list"]) for area in self.domain.area_list]
