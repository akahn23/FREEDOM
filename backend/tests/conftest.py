import asyncio
import logging
import time

import pytest

# src.freedom must be imported before src.job / src.abstract to avoid a circular import
from src import freedom  # noqa: F401
from src.repository import repository


@pytest.fixture(autouse=True)
def isolated_repository():
    """Give every test an empty global node repository and restore it afterwards."""
    saved = list(repository.data)
    repository.data.clear()
    yield repository
    repository.data[:] = saved


@pytest.fixture
def fake_log_node(mocker):
    """Register a stand-in freedom.log.Node so other nodes can call make_logger()."""
    node = object.__new__(freedom.log.Node)
    node.make_logger = mocker.Mock(return_value=mocker.Mock(spec=logging.LoggerAdapter))
    repository.append(node)
    return node


@pytest.fixture
def wait_until():
    async def _wait_until(predicate, timeout:float=1.0):
        deadline = time.monotonic() + timeout
        while not predicate():
            if time.monotonic() > deadline:
                raise AssertionError("condition not met before timeout")
            await asyncio.sleep(0.001)
    return _wait_until
