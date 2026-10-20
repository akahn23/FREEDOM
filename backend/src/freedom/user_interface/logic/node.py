# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from aiohttp import web
import asyncio
import importlib

from src import freedom, util
from src.repository import repository
from src.freedom.authz.scope import fetch_allow_set


class Node(web.View):
    def __init__(self, request:web.Request):
        """Node request
        Args:
            request (web.Request): Request
        """
        super().__init__(request)
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__name__)

    async def post(self) -> web.Response:
        """Node method execution request
        Bodies:
            domain (json_str): Domain search
            func (str): Method name
            kwargs (json_str): Arguments
        Returns:
            web.Response: Execution result
        """
        try:
            node = importlib.import_module(f"src.{self.request.match_info["node"]}").Node
            body:dict = await self.request.json()
            domain = body.get("domain", dict())
            func = body["func"]
            kwargs = body.get("kwargs", dict())
            # self._logger.info(f"post: node={self.request.match_info["node"]} {body=} {func=} {kwargs=}")
            if self.request.match_info["node"] == "freedom.map" and func == "fetch_status":
                user_id = self.request.headers.get("x-user-id")
                user_role = self.request.headers.get("x-user-role")
                if user_role == "admin":
                    # adminは全ノード閲覧可能
                    kwargs["allow_set"] = None
                elif user_id and "auth_pool" in self.request.app:
                    async with self.request.app["auth_pool"].acquire() as conn:
                        kwargs["allow_set"] = await fetch_allow_set(conn, user_id)
                elif user_id:
                    kwargs["allow_set"] = set()
            ret = getattr(repository.retrieve(node, **domain)[0], func)(**kwargs)
            if asyncio.coroutines.iscoroutine(ret):
                ret = await ret
            return web.json_response(ret, dumps=util.json.dumps)
        except Exception as e:
            self._logger.error(f"{type(e)} - {e} node={self.request.match_info["node"]} {body=}")
            return web.Response(text=str(e), status=500)
