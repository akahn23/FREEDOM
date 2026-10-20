# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import dataclasses

from src import abstract


@dataclasses.dataclass
class Domain(abstract.Domain, abc.ABC):
    """Abstract robot node settings
    Args:
        enable (bool): Enabled
        name (str): Name
        update_cycle (float): Update cycle
    Note:
        location (list[float]): Location
    """
    enable:bool = True
    name:str = ""
    update_cycle:float = 1.0

    def __post_init__(self):
        """Post-initialization processing"""
        self.location:list[float, float] = None

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return {
            "enable": {
                "type": "switch",
                "label": "有効",
            },
            "name": {
                "type": "text",
                "label": "名前",
            },
            "update_cycle": {
                "type": "number",
                "label": "更新周期",
                "suffix": "秒",
                "min": 0,
            },
        }
