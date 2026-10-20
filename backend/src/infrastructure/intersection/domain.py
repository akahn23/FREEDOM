# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import abstract, infrastructure, util


@dataclasses.dataclass
class ReserveArea(util.map.Area):
    """Reservation area settings
    Args:
        name (str): Name
        vertex_list (list[list[float]]): List of vertices
            Vertices must be ordered clockwise or counterclockwise
        priority (int): Priority
    """
    priority: int = 1


@dataclasses.dataclass
class IntersectionArea:
    """Intersection area
    Args:
        entry_area (list[util.map.Area]): Entry areas
        reserve_area (list[ReserveArea]): Reservation areas
    """
    entry_area: list[util.map.Area] = dataclasses.field(default_factory=list)
    reserve_area: list[ReserveArea] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """Post-initialization processing"""
        self.entry_area = [util.map.Area(**area) if isinstance(area, dict) else area for area in self.entry_area]
        self.reserve_area = [ReserveArea(**area) if isinstance(area, dict) else area for area in self.reserve_area]


@dataclasses.dataclass
class NodeDomain(infrastructure.Domain):
    """Intersection node settings
    Args:
        enable (bool): Enabled
        name (str): Name
        location (list[float]): Location
        priority (int): Priority
        entry_num (int): Number of robots allowed to enter
        area_list (IntersectionArea): Linked areas
        update_cycle (float): Update cycle
    """
    entry_num: int = 1
    area_list: IntersectionArea = dataclasses.field(default_factory=IntersectionArea)
    update_cycle: float = 1.0

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return super().make_form() | {
            "entry_num": {
                "type": "number",
                "label": "進入可能なロボット数",
                "min": 1,
            },
            "update_cycle": {
                "type": "number",
                "label": "更新周期",
                "suffix": "秒",
                "min": 0,
            },
            "area_list": {
                "type": "intersectionArea",
                "label": "連携エリア",
            },
        }

    def __post_init__(self):
        """Post-initialization processing"""
        super().__post_init__()
        if type(self.area_list) is dict:
            self.area_list = IntersectionArea(**self.area_list)


@dataclasses.dataclass
class Domain(abstract.Domain):
    """Intersection settings
    Args:
        node_domain (list[NodeDomain]): List of node settings
    """
    node_domain: list[NodeDomain] = dataclasses.field(default_factory=lambda: list())

    @classmethod
    def make_form(cls):
        """Create the settings form"""
        return {
            "node_domain": {
                "type": "node",
                "label": "ノード設定",
                "default": dataclasses.asdict(NodeDomain()),
                "forms": NodeDomain.make_form(),
                "unique": ["name"],
            }
        }

    def __post_init__(self):
        """Post-initialization processing"""
        self.node_domain = [NodeDomain(**node_domain) for node_domain in self.node_domain if node_domain.get("enable", False)]
