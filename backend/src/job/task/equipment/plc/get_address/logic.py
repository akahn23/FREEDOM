# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import json

from src import equipment
from src.repository import repository
from src.job.task import abstract
from src.job.task.equipment.plc.get_address import Domain


class Logic(abstract.value.Logic[Domain]):
    """Address get task logic"""

    async def init(self):
        """Called when the job starts or resumes"""
        await super().init()
        try:
            self._plc, self._address = json.loads(self.domain.address)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid address: {self.domain.address}")
        if node := repository.retrieve(equipment.plc.Node, name=self._plc):
            if not any(address.name == self._address for address in node[0].domain.bit_addresses + node[0].domain.word_addresses):
                raise ValueError(f"Address {self._address} not found in PLC {self._plc}")
        else:
            raise ValueError(f"PLC {self._plc} not found")

    async def exec(self) -> tuple[str, str]:
        """Execute the task"""
        return self._plc, self._address
