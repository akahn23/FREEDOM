# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import copy

from src import freedom
from src.job.create import Column, Domain, Interface
from src.repository import repository


class Dummy(Interface):
    def __init__(self, domain:Domain):
        """ジョブ作成ダミーDB接続
        Args:
            domain (Domain): ドメイン
        """
        self._database:list[Column] = getattr(
            repository.retrieve(freedom.main.Node)[0].domain.conf,
            "job_create",
            list()
        )

    async def fetch_name_list(self, user_id:str|None=None, is_admin:bool=False) -> list[str]:
        """ジョブ名リスト取得
        Args:
            user_id (str|None): ユーザID
            is_admin (bool): 管理者フラグ(Trueで全件取得)
        Returns:
            list[str]: ジョブ名リスト
        """
        return [row.name for row in self._database]

    async def fetch_workspace(self, name:str) -> dict:
        """Blockly環境取得
        Args:
            name (str): ジョブ名
        Returns:
            dict: Blockly環境
        """
        return copy.deepcopy(next(row.workspace for row in self._database if row.name == name))

    async def update(self, name:str, workspace:dict):
        """ジョブ更新
        Args:
            name (str): ジョブ名
            workspace (dict): Blockly環境
        """
        for row in self._database:
            if row.name == name:
                row.workspace = workspace
                return
        self._database.append(Column(name, workspace))

    async def delete(self, name:str):
        """ジョブ削除
        Args:
            name (str): ジョブ名
        """
        self._database = [row for row in self._database if row.name != name]
