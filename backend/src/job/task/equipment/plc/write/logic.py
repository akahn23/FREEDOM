# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src.repository import repository
from src import equipment
from src.job.task import abstract
from src.job.task.equipment.plc.write import Domain


class Logic(abstract.statement.Logic[Domain]):
    """PLC書き込みタスク処理"""
    async def init(self):
        """ジョブ開始・復帰時処理"""
        await super().init()
        self._plc_address = await self.domain.plc_address.make_logic(self._job_id, self._logger)
        self._data = await self.domain.data.make_logic(self._job_id, self._logger)

    async def exec(self):
        """タスク実行"""
        plc, address = await self._plc_address.exec()
        plc:equipment.plc.Node = repository.retrieve(equipment.plc.Node, name=plc)[0]
        data:bool|int = await self._data.exec()
        try:
            await plc.write(address, data, self._job_id)
        except Exception as e:
            self._logger.error(f"Error writing to PLC: {type(e)} - {e} plc={plc.domain.name} {address=} {data=}")
            raise ValueError("PLC書込み失敗")
