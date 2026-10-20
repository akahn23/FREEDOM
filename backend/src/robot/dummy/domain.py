# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import abstract, robot


@dataclasses.dataclass
class NodeDomain(robot.Domain):
    """Dummy robot node settings
    Args:
        enable (bool): Enabled
        name (str): Name
        update_cycle (float): Update cycle
    Note:
        location (list[float]): Location
    """
    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return super().make_form()


@dataclasses.dataclass
class Domain(abstract.Domain):
    """Dummy robot settings
    Args:
        node_domain (list[NodeDomain]): List of node settings
    """
    node_domain:list[NodeDomain] = dataclasses.field(default_factory=lambda:list())

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return {
            "node_domain": {
                "type": "node",
                "label": "ノード設定",
                "default": dataclasses.asdict(NodeDomain()),
                "forms": NodeDomain.make_form(),
                "unique": ["name"]
            }
        }

    def __post_init__(self):
        """Post-initialization processing"""
        self.node_domain = [NodeDomain(**node_domain) for node_domain in self.node_domain if node_domain.get("enable", False)]
