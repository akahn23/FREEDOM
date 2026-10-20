# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from src import repository
from src.equipment.iotdatashare import Node, Domain


class Repository(repository.Repository[Node]):
    """IoTDataShare repository
    Launch nodes on first run and when settings change
    Send/receive operations (with target argument)
    Attributes:
        data (list[Node]): List of nodes
        domain (Domain): Domain
    """
    def __init__(self, config:dict):
        """Instantiate
        Args:
            config (dict): Settings
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
                node.close()
        for i, node_domain in enumerate(domain.node_domain):
            if node_domain in self.domain.node_domain:
                j = self.domain.node_domain.index(node_domain)
                self.domain.node_domain.insert(i, self.domain.node_domain.pop(j))
                self.data.insert(i, self.data.pop(j))
            else:
                self.domain.node_domain.insert(i, node_domain)
                self.data.insert(i, Node(node_domain))

    def _retrieve_node(self, controller:str) -> Node:
        """Get a node
        Args:
            controller (str): Controller name
        Returns:
            Node: IoTDataShare node
        """
        try:
            return next(node for node in self.data if controller in node.domain.connect_list)
        except Exception:
            raise Exception(f'{controller} was not found')

    async def read(self, ip:str, address:str) -> int:
        """Read
        Args:
            ip (str): IP address
            address (str): Address to read
        Returns:
            str: Read result
        """
        node = self._retrieve_node(ip)
        return await node.read_item(ip, address)

    async def write(self, ip:str, address:str, data:int):
        """Write
        Args:
            ip (str): IP address
            address (str): Address to write
            data (int): Data to write
        """
        node = self._retrieve_node(ip)
        await node.write_item(ip, address, data)

    async def read_bit(self, ip:str, address:str, bit:int) -> bool:
        """Read a bit
        Args:
            ip (str): IP address
            address (str): Address to read
            bit (int): Bit to read
        Returns:
            bool: Read result
        """
        node = self._retrieve_node(ip)
        return await node.read_bit(ip, address, bit)

    async def write_bit(self, ip:str, address: str, bit:int, data:bool):
        """Write a bit
        Args:
            ip (str): IP address
            address (str): Address to write
            bit (int): Bit to write
            data (bool): Data to write
        """
        node = self._retrieve_node(ip)
        await node.write_bit(ip, address, bit, data)
