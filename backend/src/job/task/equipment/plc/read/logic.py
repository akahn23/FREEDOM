# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import equipment
from src.job.task import abstract
from src.job.task.equipment.plc.read import Domain
from src.repository import repository


class Logic(abstract.value.Logic[Domain]):
    """PLC読込みタスク処理"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()
        self._plc_address = await self.domain.plc_address.make_logic(self._job_id, self._logger)

    async def exec(self):
        """タスク実行"""
        plc, address = await self._plc_address.exec()
        plc:equipment.plc.Node = repository.retrieve(equipment.plc.Node, name=plc)[0]
        try:
            return await plc.read(address)
        except Exception as e:
            self._logger.error(f"Error reading from PLC: {type(e)} - {e} plc={plc.domain.name} {address=}")
            raise ValueError("PLC読込み失敗")
