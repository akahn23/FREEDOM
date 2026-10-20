# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import repository
from src.robot.dummy import Node, Domain


class Repository(repository.Repository[Node]):
    """ダミーロボット リポジトリ
    Attributes:
        data (list[Node]): ノードリスト
        domain (Domain): ドメイン
    """
    def __init__(self, config:dict):
        """インスタンス化
        Args:
            config (dict): 設定
        """
        if old := repository.repository.retrieve(self.__class__):
            self = old[0]
        else:
            super().__init__()
            repository.repository.append(self)
            self.domain = Domain()
        domain = Domain(**config)
        # ノードの追加・削除・順序入れ替え
        for node in list(self.data):
            if node.domain not in domain.node_domain:
                self.domain.node_domain.remove(node.domain)
                self.data.remove(node)
                node.shutdown()
        for i, node_domain in enumerate(domain.node_domain):
            if node_domain in self.domain.node_domain:
                j = self.domain.node_domain.index(node_domain)
                self.domain.node_domain.insert(i, self.domain.node_domain.pop(j))
                self.data.insert(i, self.data.pop(j))
            else:
                self.domain.node_domain.insert(i, node_domain)
                self.data.insert(i, Node(node_domain))
