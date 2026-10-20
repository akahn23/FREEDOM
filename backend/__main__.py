# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import sys
import subprocess

from src.repository import repository
from src import freedom


async def run():
    main = await freedom.main.Node.init(sys.argv[1])
    logger = repository.retrieve(freedom.log.Node)[0].make_logger(__name__)
    logger.info(f"launch: {sys.argv[1:]}")
    try:
        await main.wait_stop_requested()
    finally:
        logger.info("close")
        await main.aclose_nodes()


if __name__=="__main__":
    if len(sys.argv) < 2:
        sys.argv.append("dummy")
    if len(sys.argv) < 3:
        sys.argv.append("launch")
        while True:
            subprocess.run([sys.executable] + sys.argv)
    asyncio.run(run())
