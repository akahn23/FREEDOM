# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import importlib

from src import freedom, util
from src.freedom.map import Domain
from src.repository import repository


class Node:
    def __init__(self, config:dict):
        """地図ノード
        UIの地図情報を管理する
        Args:
            config (dict): 設定リスト
        """
        if old := repository.retrieve(self.__class__):
            repository.remove(old[0])
        self.domain = Domain(**config)
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__)
        self._logger.info(f"launch: self.domain={self.domain.__dict__}")
        repository.append(self)

    def fetch_status(self, node_name:str=None, allow_set=None) -> list[util.status.Status]:
        """状態取得
        Args:
            node_name (str): ノード名 指定なしの場合全取得
            allow_set (set[tuple[str,str]]|None): 閲覧を許可するノード Noneで絞り込み無し
        Returns:
            list[util.status.Status]: 状態リスト
        """
        ret = list()
        if node_name:
            module_list = [importlib.import_module(f"src.{node_name}")]
        else:
            module_list = list()
            structure = repository.retrieve(freedom.main.Node)[0].domain.conf.structure
            for node in structure.values():
                module_list.extend(node)
        for module in module_list:
            for node in repository.retrieve(module.Node):
                if not hasattr(node, "fetch_status"):
                    continue
                r:util.status.Status = node.fetch_status()
                if not r.node:
                    r.node = '.'.join(module.__name__.split('.')[1:])
                ret.append(r)
        # ログインユーザの閲覧可能ノードの絞り込み
        if allow_set is None:
            return ret
        if not allow_set:
            return []
        filtered: list[util.status.Status] = []
        for s in ret:
            node = s.node
            node_id = s.name
            if (node, node_id) in allow_set:
                filtered.append(s)
        return filtered
