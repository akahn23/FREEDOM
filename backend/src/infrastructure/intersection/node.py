# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import sys

from src import freedom, infrastructure, robot, util
from src.repository import repository
from src.infrastructure.intersection import NodeDomain
from src.infrastructure.command import Button


class Node(infrastructure.Node):
    """Intersection node
    Attributes:
        domain (NodeDomain): Domain
        _state (util.status.State): State
        _reserve_robot (dict[robot.Node[robot.Domain],int]): Robots holding a reservation
        _entry_robot (set[robot.Node[robot.Domain]]): Robots inside the intersection
        _exit_robot (set[robot.Node[robot.Domain]]): Robots exiting
        _logger (freedom.log.Logger): Logger
        _task (asyncio.Task): Periodic processing task
    """
    def __init__(self, domain:NodeDomain):
        """Instantiate
        Args:
            domain (NodeDomain): Domain
        """
        self.domain = domain
        self._state = util.status.State.WAITING
        self._reserve_robot:dict[robot.Node[robot.Domain],int] = dict()
        self._entry_robot:set[robot.Node[robot.Domain]] = set()
        self._exit_robot:set[robot.Node[robot.Domain]] = set()
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__, f"[{self.domain.name}]")
        self._task = asyncio.create_task(self._loop())
        self._logger.info(f"launch: {self.domain=}")

    async def _loop(self):
        """Periodic loop"""
        try:
            while sys.getrefcount(self) > 2:
                await asyncio.sleep(self.domain.update_cycle)
                self._update()
        finally:
            self._logger.info("end")

    def _update(self):
        """Update the status"""
        try:
            for r in list(self._reserve_robot.keys()):
                if r.job and util.map._is_inside(r.domain.location, self.domain.area_list.reserve_area):
                    continue
                self._reserve_robot.pop(r)
            for r in list(self._entry_robot):
                if r.job and util.map._is_inside(r.domain.location, self.domain.area_list.entry_area):
                    continue
                self._entry_robot.remove(r)
                self._exit_robot.add(r)
                self._logger.info(f"exit: robot={r.domain.name}")
            for r in list(self._exit_robot):
                if r.job:
                    if util.map._is_inside(r.domain.location, self.domain.area_list.reserve_area):
                        continue
                    if util.map._is_inside(r.domain.location, self.domain.area_list.entry_area):
                        continue
                self._exit_robot.remove(r)
        except Exception as e:
            self._logger.error(f"Failed to update: {type(e)} - {e}")

    def fetch_status(self) -> util.status.Status:
        """Get the status
        Returns:
            util.status.Status: Status
        """
        return util.status.Status(
            name=self.domain.name,
            state=util.status.State.ACTIVE if self._entry_robot else util.status.State.WAITING,
            location=self.domain.location,
            info=[f"進入中 {[r.domain.name for r in self._entry_robot]}"],
            detail=[
                f"進入中 {[r.domain.name for r in self._entry_robot]}",
                f"予約中 {[r[0].domain.name for r in sorted(self._reserve_robot.items(), key=lambda x:x[1])]}",
                f"退出中 {[r.domain.name for r in self._exit_robot]}"
            ]
        )

    def fetch_command(self) -> list:
        """Get manual operations
        Returns:
            list: Operation contents
        """
        return [
            Button(label="退出", func="exit"),
        ]

    async def accept(self, robot:robot.Node[robot.Domain]) -> bool:
        """Grant infrastructure handshake permission to a robot
        Args:
            robot (robot.Node): Robot
        """
        if not robot.domain.location:
            return True
        if robot in self._entry_robot:
            if not util.map._is_inside(robot.domain.location, self.domain.area_list.entry_area):
                self._entry_robot.remove(robot)
                self._exit_robot.add(robot)
                self._logger.info(f"exit: robot={robot.domain.name}")
        elif robot in self._exit_robot:
            if not util.map._is_inside(robot.domain.location, self.domain.area_list.reserve_area):
                if not util.map._is_inside(robot.domain.location, self.domain.area_list.entry_area):
                    self._exit_robot.remove(robot)
        else:
            priority = None
            for reserve_area in self.domain.area_list.reserve_area:
                if util.map._is_inside(robot.domain.location, [reserve_area]):
                    if priority is None or priority < reserve_area.priority:
                        priority = reserve_area.priority
            if priority is None:
                self._reserve_robot.pop(robot, None)
            else:
                if robot not in self._reserve_robot.keys():
                    self._logger.info(f"reserve: robot={robot.domain.name} {priority=}")
                self._reserve_robot[robot] = priority
            if util.map._is_inside(robot.domain.location, self.domain.area_list.entry_area):
                if robot in self._reserve_robot.keys():
                    if len(self._entry_robot) >= self.domain.entry_num:
                        return False
                    if robot != max(self._reserve_robot, key=self._reserve_robot.get):
                        return False
                    self._reserve_robot.pop(robot)
                    self._entry_robot.add(robot)
                    self._logger.info(f"entry: robot={robot.domain.name}")
                else:
                    self._exit_robot.add(robot)
                    self._logger.info(f"exit: robot={robot.domain.name}")
        return True

    async def cancel(self, robot:robot.Node[robot.Domain]) -> bool:
        """End the infrastructure handshake for a robot
        Args:
            robot (robot.Node): Robot node
        """
        self._reserve_robot.pop(robot, None)
        self._entry_robot.discard(robot)
        self._exit_robot.discard(robot)

    def exit(self):
        """Exit"""
        self._exit_robot.update(self._entry_robot)
        self._entry_robot.clear()
        self._logger.info(f"exit")
