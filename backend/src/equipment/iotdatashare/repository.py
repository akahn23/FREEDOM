# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import repository
from src.equipment.iotdatashare import Node, Domain


class Repository(repository.Repository[Node]):
    """IoTDataShare リポジトリ
    初回and設定変更時ノード起動
    各種送受信処理(接続先引数付き)
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

    def _retrieve_node(self, controller:str) -> Node:
        """ノード取得
        Args:
            controller (str): コントローラ名
        Returns:
            Node: IoTDataShareノード
        """
        try:
            return next(node for node in self.data if controller in node.domain.connect_list)
        except Exception:
            raise Exception(f'{controller} was not found')

    async def read(self, ip:str, address:str) -> int:
        """読込み
        Args:
            ip (str): IPアドレス
            address (str): 読込みアドレス
        Returns:
            str: 読込み結果
        """
        node = self._retrieve_node(ip)
        return await node.read_item(ip, address)

    async def write(self, ip:str, address:str, data:int):
        """書込み
        Args:
            ip (str): IPアドレス
            address (str): 書込みアドレス
            data (int): 書込み内容
        """
        node = self._retrieve_node(ip)
        await node.write_item(ip, address, data)

    async def read_bit(self, ip:str, address:str, bit:int) -> bool:
        """ビット読込み
        Args:
            ip (str): IPアドレス
            address (str): 読込みアドレス
            bit (int): 読込みビット
        Returns:
            bool: 読込み結果
        """
        node = self._retrieve_node(ip)
        return await node.read_bit(ip, address, bit)

    async def write_bit(self, ip:str, address: str, bit:int, data:bool):
        """ビット書込み
        Args:
            ip (str): IPアドレス
            address (str): 書込みアドレス
            bit (int): 書込みビット
            data (bool): 書込み内容
        """
        node = self._retrieve_node(ip)
        await node.write_bit(ip, address, bit, data)
