# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc

from src.freedom.main import Domain


class Interface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, domain:Domain):
        """Settings database connection interface
        Args:
            domain (Domain): Domain
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def fetch(self, node:str) -> dict:
        """Get the settings
        Return None if not found
        Args:
            node (str): Node name
        Returns:
            dict: Settings
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def update(self, node:str, config:dict):
        """Update the settings
        Args:
            node (str): Node name
            config (dict): Settings
        """
        raise NotImplementedError()
