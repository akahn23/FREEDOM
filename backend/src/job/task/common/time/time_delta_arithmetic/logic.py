# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

from src.job.task import abstract
from src.job.task.common.time.time_delta_arithmetic import Domain


class Logic(abstract.value.Logic[Domain]):
    """時間差分計算処理"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()
        self._LEFT = await self.domain.LEFT.make_logic(self._job_id, self._logger)
        self._RIGHT = await self.domain.RIGHT.make_logic(self._job_id, self._logger)

    async def exec(self):
        """タスク実行"""
        LEFT:datetime = await self._LEFT.exec()
        RIGHT:datetime = await self._RIGHT.exec()
        operator = self.domain.operator
        try:
            if operator == "+":
                return LEFT + RIGHT
            if operator == "-":
                return LEFT - RIGHT
            if operator == "×":
                return LEFT * RIGHT
            if operator == "÷":
                return LEFT / RIGHT
        except Exception as e:
            self._logger.error(f"Failed to time_delta_arithmetic: {type(e)} - {e} {LEFT} {operator} {RIGHT}")
            raise Exception("時間計算の演算に失敗")
