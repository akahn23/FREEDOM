# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import importlib

from src.freedom.main import Interface, Domain


class Dummy(Interface):
    def __init__(self, domain:Domain):
        """Dummy settings database connection
        Args:
            domain (Domain): Domain
        """
        self._database = domain.conf.freedom_main

    async def fetch(self, node:str) -> dict:
        """Get the settings
        Return None if not found
        Args:
            node (str): Node name
        Returns:
            dict: Settings
        """
        return self._database.get(importlib.import_module(f"src.{node}"), None)

    async def update(self, node:str, config:dict):
        """Update the settings
        Args:
            node (str): Node name
            config (dict): Settings
        """
        self._database[importlib.import_module(f"src.{node}")] = config
