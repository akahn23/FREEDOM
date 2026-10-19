# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import importlib

from src.freedom.main import Domain, Interface


class Dummy(Interface):
    def __init__(self, domain:Domain):
        """ダミー設定DB接続
        Args:
            domain (Domain): ドメイン
        """
        self._database = domain.conf.freedom_main

    async def fetch(self, node:str) -> dict:
        """設定取得
        無ければNoneを返す
        Args:
            node (str): ノード名
        Returns:
            dict: 設定
        """
        return self._database.get(importlib.import_module(f"src.{node}"), None)

    async def update(self, node:str, config:dict):
        """設定更新
        Args:
            node (str): ノード名
            config (dict): 設定
        """
        self._database[importlib.import_module(f"src.{node}")] = config
