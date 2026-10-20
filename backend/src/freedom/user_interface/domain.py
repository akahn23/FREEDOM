# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from src import abstract, freedom
from src.repository import repository


@dataclasses.dataclass
class Domain(abstract.Domain):
    """User interface settings
    Args:
        ip (str): Target IP address
        port (int): Target port number
        origin (list[str]): List of allowed origins for CORS
            Defined as InitVar because it should be part of the startup config but not saved to the settings database
        sub_title (str): Subtitle
        update_cycle (float): Update cycle
    """
    ip:dataclasses.InitVar[str] = None
    port:dataclasses.InitVar[int] = None
    origin:dataclasses.InitVar[list[str]] = None
    sub_title:str = ""
    update_cycle:float = 3

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return {
            "sub_title": {
                "type": "text",
                "label": "Freedomサブタイトル名",
            },
            "update_cycle": {
                "type": "number",
                "label": "更新周期",
                "suffix": "秒",
                "min": 0,
            },
        }

    def __post_init__(self, ip:str=None, port:int=None, origin:list[str]=None):
        """Post-initialization processing
        Args:
            ip (str): Target IP address
            port (int): Target port number
            origin (list[str]): List of allowed origins for CORS
        """
        if conf := repository.retrieve(freedom.main.Node):
            conf = conf[0].domain.conf.user_interface
            self.ip = conf.ip
            self.port = conf.port
            self.origin = conf.origin
        else:
            self.ip = ip
            self.port = port
            self.origin = origin
