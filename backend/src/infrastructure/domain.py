# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import dataclasses

from src import abstract


@dataclasses.dataclass
class Domain(abstract.Domain, abc.ABC):
    """Abstract infrastructure equipment node settings
    Args:
        enable (bool): Enabled
        name (str): Name
        location (list[float]): Location
        priority (int): Priority
    """
    enable:bool = True
    name:str = ""
    location:list[float, float] = dataclasses.field(default_factory=lambda:[0.0,0.0])
    priority:int = 0

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
            "location": {
                "type": "location",
                "label": "位置",
            },
            "priority": {
                "type": "number",
                "label": "優先度",
                "integer": True,
            },
        }
