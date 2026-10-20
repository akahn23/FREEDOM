# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from aiohttp import web
import importlib

from src import freedom, util
from src.repository import repository


class Domain(web.View):
    def __init__(self, request:web.Request):
        """Domain request
        Args:
            request (web.Request): Request
        """
        super().__init__(request)
        self._logger = repository.retrieve(freedom.log.Node)[0].make_logger(__name__)

    async def post(self) -> web.Response:
        """Domain get request
        Bodies:
            Domain search
        Returns:
            web.Response: List of domains
        """
        try:
            node = importlib.import_module(f"src.{self.request.match_info["node"]}").Node
            body = await self.request.json() if self.request.can_read_body else dict()
            return web.json_response([node.domain for node in repository.retrieve(node, **body)], dumps=util.json.dumps)
        except Exception as e:
            self._logger.error(f"get: {type(e)} - {e} node={self.request.match_info["node"]} {body=}")
            return web.Response(text=f"{type(e)} - {e}", status=500)
