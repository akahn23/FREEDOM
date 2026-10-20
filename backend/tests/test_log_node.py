import asyncio
import dataclasses
import logging
from datetime import datetime, timezone

import pytest

from src import freedom
from src.freedom.log import Column, Domain, Interface, access
from src.repository import repository

LogNode = freedom.log.Node


class RecordingAccess(Interface):
    """In-memory stand-in for a log DB; optionally fails the first N inserts."""

    def __init__(self, domain=None, fail_times:int=0):
        self.batches: list[list[Column]] = []
        self.fail_times = fail_times
        self.calls = 0

    async def insert(self, log_list):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ConnectionError("db down")
        # Node._loop clears the list it passes in after insert, so keep a copy
        self.batches.append(list(log_list))

    async def fetch(self, *args, **kwargs):
        return []

    def messages(self, name:str) -> list[str]:
        return [row.message for batch in self.batches for row in batch if row.name == name]


def _detach_handlers(node):
    for logger in [logging.getLogger(name) for name in logging.root.manager.loggerDict] + [logging.root]:
        for handler in list(logger.handlers):
            if handler in (node._stream_handler, node._output_handler):
                logger.removeHandler(handler)


@pytest.fixture
async def log_node():
    node = LogNode()
    yield node
    node._task.cancel()
    await asyncio.gather(node._task, return_exceptions=True)
    _detach_handlers(node)


def _column(message:str, minute:int=0) -> Column:
    return Column(datetime(2026, 1, 1, 0, minute, tzinfo=timezone.utc), "test", "INFO", message)


# --- construction / config -------------------------------------------------

async def test_first_init_registers_node_and_starts_loop(log_node):
    assert repository.retrieve(LogNode) == [log_node]
    assert isinstance(log_node.domain, Domain)
    assert log_node._access is None
    assert not log_node._task.done()


async def test_reinit_updates_existing_node_instead_of_registering_new_one(log_node):
    LogNode({"interface": "Dummy", "retention_period": 7})

    assert repository.retrieve(LogNode) == [log_node]
    assert log_node.domain.interface == "Dummy"
    assert log_node.domain.retention_period == 7
    assert isinstance(log_node._access, access.Dummy)


# --- make_logger / batch write --------------------------------------------

async def test_make_logger_buffers_records_as_columns(log_node):
    logger = log_node.make_logger("tests.log_node.buffer", prefix="robot.dummy")
    logger.warning("hello")

    assert len(log_node._log_list) == 1
    col = log_node._log_list[0]
    assert (col.name, col.levelname, col.message) == ("tests.log_node.buffer", "WARNING", '"robot.dummy hello"')
    assert isinstance(col.time, datetime)


async def test_make_logger_without_prefix_quotes_message(log_node):
    log_node.make_logger("tests.log_node.noprefix").info("plain")

    assert log_node._log_list[0].message == '"plain"'


async def test_loop_holds_logs_until_access_is_configured(log_node, wait_until):
    logger = log_node.make_logger("tests.log_node.pending")
    logger.info("one")
    logger.info("two")
    await wait_until(lambda: not log_node._log_list)

    fake = RecordingAccess()
    log_node._access = fake
    await wait_until(lambda: len(fake.messages("tests.log_node.pending")) == 2)

    assert fake.messages("tests.log_node.pending") == ['"one"', '"two"']
    assert fake.messages("src.freedom.log") == ['"launch"']


async def test_loop_writes_buffered_logs_in_batches(log_node, wait_until):
    fake = RecordingAccess()
    log_node._access = fake
    logger = log_node.make_logger("tests.log_node.batch")

    logger.info("a")
    logger.info("b")
    await wait_until(lambda: len(fake.messages("tests.log_node.batch")) == 2)
    logger.info("c")
    await wait_until(lambda: len(fake.messages("tests.log_node.batch")) == 3)

    assert fake.messages("tests.log_node.batch") == ['"a"', '"b"', '"c"']
    assert all(batch for batch in fake.batches)
    assert log_node._log_list == []


async def test_loop_retries_failed_insert_without_losing_or_duplicating_logs(log_node, wait_until):
    fake = RecordingAccess(fail_times=3)
    log_node._access = fake
    logger = log_node.make_logger("tests.log_node.retry")

    logger.error("boom")
    await wait_until(lambda: fake.messages("tests.log_node.retry"))
    logger.error("after")
    await wait_until(lambda: len(fake.messages("tests.log_node.retry")) == 2)

    assert fake.calls >= 4
    assert fake.messages("tests.log_node.retry") == ['"boom"', '"after"']


async def test_loop_stops_on_cancel(log_node):
    log_node._task.cancel()
    await asyncio.gather(log_node._task, return_exceptions=True)

    assert log_node._task.done()


# --- fetch ------------------------------------------------------------------

@pytest.fixture
def fetch_node(mocker):
    node = object.__new__(LogNode)
    node._access = mocker.Mock(spec=Interface)
    node._access.fetch = mocker.AsyncMock(return_value=[])
    return node


async def test_fetch_parses_times_and_applies_defaults(fetch_node):
    await fetch_node.fetch("2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00")

    fetch_node._access.fetch.assert_awaited_once_with(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        100, None, None, None, "time", "desc",
    )


@pytest.mark.parametrize(("kwargs", "expected"), [
    ({"row_count": 25}, 25),
    ({"row_count": None}, 100),
    ({"row_count": "null"}, 100),
    ({"row_count": 25, "all_rows": True}, None),
])
async def test_fetch_effective_row_count(fetch_node, kwargs, expected):
    await fetch_node.fetch("2026-01-01T00:00:00", "2026-01-02T00:00:00", **kwargs)

    assert fetch_node._access.fetch.await_args.args[2] == expected


async def test_fetch_forwards_cursor_filters_and_sort(fetch_node):
    await fetch_node.fetch(
        "2026-01-01T00:00:00", "2026-01-02T00:00:00",
        cursor_time="2026-01-01T12:00:00",
        keywords=["  robot ", "", "   ", 3, "lamp"],
        levelnames=["ERROR"],
        sort_field="name",
        sort_direction="asc",
    )

    args = fetch_node._access.fetch.await_args.args
    assert args[3] == datetime(2026, 1, 1, 12)
    assert args[4:] == (["robot", "lamp"], ["ERROR"], "name", "asc")


@pytest.mark.parametrize("keywords", [None, [], ["", "  "]])
def test_normalize_keywords_returns_none_when_empty(keywords):
    assert LogNode._normalize_keywords(keywords) is None


async def test_fetch_returns_plain_dicts(fetch_node):
    fetch_node._access.fetch.return_value = [_column("m")]

    ret = await fetch_node.fetch("2026-01-01T00:00:00", "2026-01-02T00:00:00")

    assert ret == [dataclasses.asdict(_column("m"))]


async def test_fetch_rejects_invalid_iso_time(fetch_node):
    with pytest.raises(ValueError):
        await fetch_node.fetch("yesterday", "2026-01-02T00:00:00")
    fetch_node._access.fetch.assert_not_awaited()


async def test_fetch_end_to_end_with_dummy_access():
    node = object.__new__(LogNode)
    node._access = access.Dummy(Domain(interface="Dummy"))
    await node._access.insert([
        Column(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc), "robot.dummy", "INFO", "moving"),
        Column(datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc), "robot.dummy", "ERROR", "stuck"),
        Column(datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc), "infrastructure.lamp", "INFO", "on"),
    ])

    ret = await node.fetch(
        "2026-01-01T00:00:00+00:00", "2026-01-01T01:00:00+00:00",
        keywords=["robot"], sort_direction="asc",
    )
    assert [r["message"] for r in ret] == ["moving", "stuck"]

    ret = await node.fetch(
        "2026-01-01T00:00:00+00:00", "2026-01-01T01:00:00+00:00",
        levelnames=["INFO"], row_count=1,
    )
    assert [r["message"] for r in ret] == ["on"]
