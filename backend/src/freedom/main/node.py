# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import dataclasses
import importlib
import typing

from src.repository import repository, Repository
from src import abstract, freedom
from src.freedom.main import Interface, access
if typing.TYPE_CHECKING:
    import config.dummy


class Node(abstract.Node):
    @classmethod
    async def init(cls, config_name:str) -> "Node":
        """初回システム構築
        Args:
            config_name (str): 設定ファイル名
        Returns:
            Node: システムノード
        """
        freedom.log.Node.configure()
        self = cls(config_name)
        await self._init_task
        await self.update_node("freedom.map")
        await self.update_node("freedom.user_interface")
        for node_list in self.domain.conf.structure.values():
            for node in node_list:
                try:
                    node_name = '.'.join(node.__name__.split('.')[1:])
                    await self.update_node(node_name)
                except Exception as e:
                    self._logger.error(f"Failed to make node: {node_name=} {type(e)} - {e}")
        return self

    def __init__(self, config_name:str):
        """Freedomシステムノード
        各ノードの起動や更新を行う
        Args:
            config_name (str): 設定ファイル名
        """
        conf:config.dummy = importlib.import_module(f"config.{config_name}")
        self.domain = conf.main
        self.domain.conf = conf
        self._access:Interface = getattr(access, self.domain.interface)(self.domain)
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__)
        self._stop_requested = asyncio.Event()
        self._init_task = asyncio.create_task(self._init_loop())
        self._logger.info(f"launch: {self.domain}")
        repository.append(self)

    async def _init_loop(self):
        """初期処理ループ"""
        while True:
            try:
                await self.update_node("freedom.log")
                break
            except Exception:
                await asyncio.sleep(0)

    def fetch_structure(self) -> dict[str, list[str]]:
        """ノード構造取得
        Returns:
            dict[str, list[str]]: ノード構造
        """
        ret = dict()
        for k,v in self.domain.conf.structure.items():
            ret['.'.join(k.__name__.split('.')[1:])] = ['.'.join(i.__name__.split('.')[1:]) for i in v]
        return ret

    async def fetch_form(self, node:str) -> dict:
        """フォーム取得
        Args:
            node (str): ノード名
        Returns:
            dict: フォーム
        """
        domain:abstract.Domain = getattr(importlib.import_module(f"src.{node}"), "Domain")
        return domain.make_form()

    async def fetch_config(self, node:str) -> dict:
        """設定取得
        Args:
            node (str): ノード名
        Returns:
            dict: 設定
        """
        return await self._access.fetch(node)

    async def restart(self, version:str):
        """プログラム再起動
        Args:
            version (str): バージョン名
        """
        # TODO: git checkout
        self._logger.info(f"restart: {version=}")
        self._stop_requested.set()

    async def wait_stop_requested(self):
        """停止要求(restart)まで待つ"""
        await self._stop_requested.wait()

    async def aclose_nodes(self):
        """全ノード停止
        構築と逆順に停止完了まで待つ ログノードは最後に停止する
        """
        for item in reversed(list(repository)):
            if item is self or isinstance(item, freedom.log.Node):
                continue
            await self._aclose_tree(item)
        await abstract.lifecycle.aclose(self._access)
        for node in repository.retrieve(freedom.log.Node):
            await node.aclose()

    @classmethod
    async def _aclose_tree(cls, item):
        """ノード停止 リポジトリは配下のノードも停止する
        Args:
            item (typing.Any): ノードまたはリポジトリ
        """
        await abstract.lifecycle.aclose(item)
        if isinstance(item, Repository):
            for child in reversed(list(item)):
                await cls._aclose_tree(child)

    async def update_node(self, node:str, config:dict=None):
        """ノード更新
        DBに挿入後、ノード構築を行う
        Args:
            node (str): ノード名
            config (typing.Any): 設定
        """
        module = importlib.import_module(f"src.{node}")
        if config is not None:
            await self._access.update(node, config)
            self._logger.info(f"update {node=} {config=}")
        elif (config:=await self._access.fetch(node)) is None:
            await self.update_node(node, dataclasses.asdict(getattr(module, "Domain")()))
            return
        if hasattr(module, "Repository"):
            node_cls:type[abstract.Node] = getattr(module, "Repository")
        else:
            node_cls:type[abstract.Node] = getattr(module, "Node")
        if hasattr(node_cls, "configure"):
            node_cls.configure(config)
        else:
            node_cls(config)
