# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import inspect
import importlib
import asyncio

from src import abstract, freedom, job
from src.repository import repository
from src.job.create import Domain, Interface, access


class Node(abstract.Node):
    def __init__(self, config:dict):
        """Job creation node
        Args:
            config (dict): Settings
        """
        if old := repository.retrieve(self.__class__):
            repository.remove(old[0])
        self.domain = Domain(**config)
        self._access:Interface = getattr(access, self.domain.interface)(self.domain)
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__package__)
        self._logger.info(f"launch: {self.domain}")
        repository.append(self)

    def _parse_block(self, block:dict) -> dict:
        """Analyze block contents
        Recursive helper
        Args:
            block (dict): Block contents
        Returns:
            dict: Task contents
        """
        fields:dict = block.get("fields", dict())
        inputs:dict[str,dict] = dict()
        for key, value in block.get("inputs", dict()).items():
            input_block = value.get("block") or value.get("shadow", dict())
            inputs[key] = self._parse_block(input_block)
        ret =  {
            "type": block["type"],
            "id": block["id"],
            **fields,
            **inputs
        }
        if "next" in block:
            ret["next"] = self._parse_block(block["next"]["block"])
        return ret

    def _to_task(self, workspace:dict) -> tuple[dict, list[dict]]:
        """Convert a Blockly workspace to tasks
        Only the first job is processed
        Args:
            workspace (dict): Blockly workspace
        Returns:
            tuple[dict, list]: Task contents, task variables
        """
        blocks = workspace.get("blocks", dict()).get("blocks", list())
        task = self._parse_block(blocks[0]) if blocks else dict()
        return task, workspace.get("variables", list())

    async def fetch_define(self) -> tuple[list[dict], list[dict]]:
        """Get block and toolbox definitions
        Returns:
            tuple[list[dict], list[dict]]: Block definitions, toolbox definitions
        """
        node_name:list[str] = list()
        structure = repository.retrieve(freedom.main.Node)[0].domain.conf.structure
        for key,value in structure.items():
            node_name.append('.'.join(key.__name__.split('.')[1:]))
            node_name.extend(['.'.join(v.__name__.split('.')[1:]) for v in value])
        node_name.extend('.'.join(m.__name__.split('.')[3:]) for _,m in inspect.getmembers(job.task.common, inspect.ismodule))
        block = list()
        category = list()
        for node in node_name:
            try:
                module = importlib.import_module(f"src.job.task.{node}")
            except Exception:
                continue
            contents = list()
            for _, task in inspect.getmembers(module, inspect.ismodule):
                if not hasattr(task, "Domain"):
                    continue
                domain:type[job.task.abstract.value.Domain] = getattr(task, "Domain")
                define_block_result = domain.define_block()
                if asyncio.coroutines.iscoroutine(define_block_result):
                    define_block_result = await define_block_result
                block.extend(define_block_result)
                contents.extend(domain.define_toolbox())
            if contents:
                category.append({
                    "kind": "category",
                    "name": node,
                    "colour": block[-1].get("colour"),
                    "contents": contents
                })
        toolbox = {
            "kind": "categoryToolbox",
            "contents": category
        }
        return block, toolbox

    async def fetch_name_list(self, user_id:str|None=None, is_admin:bool=False) -> list[str]:
        """Get the list of job names
        Args:
            user_id (str|None): User ID
            is_admin (bool): Admin flag (True fetches all)
        Returns:
            list[str]: List of job names
        """
        return await self._access.fetch_name_list(user_id=user_id, is_admin=is_admin)

    async def fetch_workspace(self, name:str) -> dict:
        """Get the Blockly workspace
        Args:
            name (str): Job name
        Returns:
            dict: Blockly workspace
        """
        return await self._access.fetch_workspace(name)

    async def update(self, name:str, workspace:dict):
        """Save a job
        Args:
            name (str): Job name
            workspace (dict): Blockly workspace
        """
        await self._access.update(name, workspace)
        self._logger.info(f"update: {name=} {workspace=}")

    async def delete(self, name:str):
        """Delete a job
        Args:
            name (str): Job name
        """
        await self._access.delete(name)
        self._logger.info(f"delete: {name=}")

    async def active(self, name:str, **kwargs) -> str:
        """Run a job
        Args:
            name (str): Job name
            **kwargs (dict): Initial values of task variables
        Returns:
            str: Job ID
        """
        workspace = await self._access.fetch_workspace(name)
        task, variables = self._to_task(workspace)
        for var in variables:
            var["value"] = kwargs.get(var.get("name"))
        self._logger.info(f"to_task: {name=} {task=} {variables=}")
        return await repository.retrieve(job.active.Repository)[0].insert(name, task, variables)
