# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import logging
import pathlib
import sys
from types import SimpleNamespace

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# src.freedom must be imported before src.job / src.abstract to avoid a circular import.
from src import freedom  # noqa: E402,F401
from src import job  # noqa: E402
from src.job.task import abstract  # noqa: E402
from src.repository import repository  # noqa: E402


def pytest_configure(config):
    """Run coroutine tests under pytest-asyncio without an ini file (`pytest backend/tests` from anywhere)."""
    if config.getoption("asyncio_mode", None) is None:
        config.option.asyncio_mode = "auto"


@pytest.fixture(autouse=True)
def _block_real_database(monkeypatch):
    """Fail fast if any code under test tries to open a real PostgreSQL connection."""
    import asyncpg

    async def _refuse(*args, **kwargs):
        raise AssertionError("unit tests must not connect to a real database")

    monkeypatch.setattr(asyncpg, "create_pool", _refuse)
    monkeypatch.setattr(asyncpg, "connect", _refuse)


@pytest.fixture
def clean_repository():
    """Empty the global node repository for the test and restore it afterwards."""
    saved = list(repository.data)
    repository.data.clear()
    yield repository
    repository.data[:] = saved


@pytest.fixture
def active_job(clean_repository):
    """A job.active.Node stand-in registered in the repository (no event loop task, no DB)."""
    node = object.__new__(job.active.Node)
    node.domain = SimpleNamespace(
        id="job-1",
        name="test job",
        variables=[],
        error_msg=set(),
        warning_msg=set(),
    )
    clean_repository.append(node)
    return node


@pytest.fixture
def logger():
    return logging.getLogger("freedom.tests")


@pytest.fixture
def build_logic(logger):
    """Build a task Logic from a Blockly-style dict, as job.active does at job start."""
    async def _build(content: dict, job_id: str = "job-1"):
        domain = abstract.value.Domain.to_domain(content)
        return await domain.make_logic(job_id, logger)
    return _build
