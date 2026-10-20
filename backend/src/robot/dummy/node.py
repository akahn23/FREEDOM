# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import sys

from src import freedom, robot, util
from src.repository import repository
from src.robot.dummy import NodeDomain


class Node(robot.Node[NodeDomain]):
    def __init__(self, domain:NodeDomain):
        super().__init__(domain)
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__, f"[{self.domain.name}]")
        self._task = asyncio.create_task(self._loop())
        self._logger.info(f"launch: {self.domain=}")

    async def _loop(self):
        while sys.getrefcount(self) > 2:
            try:
                await asyncio.gather(
                    asyncio.sleep(self.domain.update_cycle),
                    self._update(),
                )
            except asyncio.CancelledError:
                break
        self._logger.info("close")

    def fetch_status(self) -> util.status.Status:
        """Get the status
        Returns:
            util.status.Status: Status
        """
        info = list()
        if self.job:
            if self.job.domain.error_msg:
                state = util.status.State.ERROR
                info.extend(list(self.job.domain.error_msg))
            elif self.job.domain.warning_msg:
                state = util.status.State.WARNING
                info.extend(list(self.job.domain.warning_msg))
            else:
                state = util.status.State.ACTIVE
                info.append(f"{self.job.domain.name} 実行中")
        else:
            state = util.status.State.WAITING
        return util.status.Status(
            name=self.domain.name,
            state=state,
            location=self.domain.location,
            info=info,
        )
