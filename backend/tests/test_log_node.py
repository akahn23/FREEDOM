import asyncio
from datetime import datetime
import logging

import pytest

from src.freedom.log import Column
from src.freedom.log.node import Node


class FakeAccess:
    def __init__(self, fail_times:int=0, exc:Exception|None=None):
        self.fail_times = fail_times
        self.exc = exc or ConnectionError("db down")
        self.calls = 0
        self.written:list[Column] = []

    async def insert(self, log_list):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.exc
        self.written.extend(log_list)


def make_node(access=None) -> Node:
    node = object.__new__(Node)
    node._log_list = []
    node._access = access
    node._writer_logger = logging.getLogger("test.freedom.log.writer")
    node.RETRY_BASE_DELAY = 0.001
    node.RETRY_MAX_DELAY = 0.004
    node.MAX_CONSECUTIVE_FAILURES = 3
    node.SHUTDOWN_FLUSH_TIMEOUT = 1.0
    return node


def col(message:str) -> Column:
    return Column(datetime.now(), "test", "INFO", message)


async def wait_until(predicate, timeout:float=2.0):
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.001)


async def stop(task:asyncio.Task):
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def test_backoff_is_exponential_and_capped():
    node = make_node()
    node.RETRY_BASE_DELAY = 0.5
    node.RETRY_MAX_DELAY = 30.0
    assert [node._backoff_delay(n) for n in range(1, 9)] == [0.5, 1, 2, 4, 8, 16, 30, 30]


async def test_transient_failure_is_retried_without_losing_logs(caplog):
    access = FakeAccess(fail_times=2)
    node = make_node(access)
    node._log_list.extend([col("a"), col("b")])
    with caplog.at_level(logging.DEBUG, logger="test.freedom.log.writer"):
        task = asyncio.create_task(node._loop())
        await wait_until(lambda: access.written)
        await stop(task)
    assert [c.message for c in access.written] == ["a", "b"]
    assert access.calls == 3
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 2
    assert warnings[0].exc_info is not None
    assert any("recovered" in r.getMessage() for r in caplog.records)


async def test_persistent_failure_drops_batch_loudly_and_keeps_running(caplog):
    access = FakeAccess(fail_times=3)
    node = make_node(access)
    node._log_list.append(col("poison"))
    with caplog.at_level(logging.DEBUG, logger="test.freedom.log.writer"):
        task = asyncio.create_task(node._loop())
        await wait_until(lambda: access.calls >= 3)
        node._log_list.append(col("next"))
        await wait_until(lambda: access.written)
        await stop(task)
    assert [c.message for c in access.written] == ["next"]
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 1
    assert "dropping 1 logs" in errors[0].getMessage()
    assert errors[0].exc_info[0] is ConnectionError


async def test_cancel_flushes_buffered_logs():
    access = FakeAccess()
    node = make_node(access)
    task = asyncio.create_task(node._loop())
    await asyncio.sleep(0)
    node._log_list.append(col("last words"))
    await stop(task)
    assert [c.message for c in access.written] == ["last words"]
    assert node._log_list == []


async def test_cancel_during_retry_flushes_in_flight_batch():
    access = FakeAccess(fail_times=1)
    node = make_node(access)
    node.RETRY_BASE_DELAY = node.RETRY_MAX_DELAY = 60
    node._log_list.append(col("in flight"))
    task = asyncio.create_task(node._loop())
    await wait_until(lambda: access.calls == 1)
    node._log_list.append(col("queued"))
    await stop(task)
    assert [c.message for c in access.written] == ["in flight", "queued"]


async def test_flush_failure_on_shutdown_is_logged_with_traceback(caplog):
    access = FakeAccess(fail_times=99)
    node = make_node(access)
    node._log_list.append(col("x"))
    with caplog.at_level(logging.DEBUG, logger="test.freedom.log.writer"):
        await node._flush([])
    [record] = caplog.records
    assert "failed to flush 1 logs" in record.getMessage()
    assert record.exc_info[0] is ConnectionError


async def test_flush_without_access_reports_unwritten_logs(caplog):
    node = make_node()
    node._log_list.append(col("x"))
    with caplog.at_level(logging.DEBUG, logger="test.freedom.log.writer"):
        await node._flush([])
    assert "1 logs not written" in caplog.records[0].getMessage()


def test_buffer_is_bounded_and_drops_oldest(caplog):
    node = make_node()
    node.MAX_BUFFERED_LOGS = 2
    handler_list = node._log_list
    node._log_list.extend([col("1"), col("2"), col("3")])
    with caplog.at_level(logging.DEBUG, logger="test.freedom.log.writer"):
        node._trim_buffer()
    assert node._log_list is handler_list
    assert [c.message for c in node._log_list] == ["2", "3"]
    assert "dropped 1 oldest" in caplog.records[0].getMessage()
