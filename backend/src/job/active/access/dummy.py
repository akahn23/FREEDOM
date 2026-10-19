# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import uuid
from datetime import datetime

from src import freedom
from src.job.active import Domain, Interface, NodeDomain
from src.repository import repository


class Dummy(Interface):
    def __init__(self, domain:Domain):
        """ジョブ実行ダミーDB接続
        Args:
            domain (Domain): ドメイン
        """
        self._database:list[NodeDomain] = getattr(
            repository.retrieve(freedom.main.Node)[0].domain.conf,
            "job_active",
            list()
        )

    async def insert(self, name:str, task:dict, variables:list[dict]) -> dict:
        """実行ジョブ保存
        Args:
            name (str): ジョブ名
            task (dict): タスク内容
            variables (list[dict]): タスク変数
        Returns:
            dict: 実行ジョブ設定
        """
        domain = NodeDomain(uuid.uuid4(), datetime.now(), name, task, variables)
        self._database.append(domain)
        return dataclasses.asdict(domain)

    async def fetch(self) -> list[dict]:
        """実行ジョブ取得
        Returns:
            list[dict]: 実行ジョブ設定
        """
        return [dataclasses.asdict(domain) for domain in self._database]

    async def update(self, node_list:list[NodeDomain]):
        """実行ジョブ更新
        Args:
            node_list (list[NodeDomain]): 実行ジョブリスト
        """
        self._database = node_list
