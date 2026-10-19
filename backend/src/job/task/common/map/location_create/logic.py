# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.job.task import abstract
from src.job.task.common.map.location_create import Domain


class Logic(abstract.value.Logic[Domain]):
    """位置設定タスク処理"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()

    async def exec(self) -> list[float, float]:
        """タスク実行"""
        return self.domain.location
