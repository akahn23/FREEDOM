import re
from datetime import datetime, timedelta, timezone

import pytest

from src.freedom.log import Column, Domain
from src.freedom.log.access import PostgreSQL

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 1, 2, tzinfo=timezone.utc)


def _sql(query:str) -> str:
    return re.sub(r"\s+", " ", query).strip()


@pytest.fixture
def pg(mocker):
    """PostgreSQL log access with a fake asyncpg pool (no live database)."""
    obj = object.__new__(PostgreSQL)
    obj._domain = Domain(interface="PostgreSQL", schema="freedom", table="freedom_log", retention_period=2)
    obj._logger = mocker.Mock()
    obj._pool = mocker.Mock()
    obj._pool.fetch = mocker.AsyncMock(return_value=[])
    obj._pool.fetchval = mocker.AsyncMock(return_value="UTC")
    obj._pool.execute = mocker.AsyncMock()
    obj._pool.executemany = mocker.AsyncMock()
    obj._last_time = datetime(2026, 1, 1)
    return obj


# --- query building ----------------------------------------------------------

def test_keyword_conditions_and_terms_within_item_or_across_items():
    conditions, params, nxt = PostgreSQL._build_keyword_conditions(["robot error", "lamp"], 3)

    assert params == ["%robot%", "%error%", "%lamp%"]
    assert nxt == 6
    assert len(conditions) == 2
    assert conditions[0].count(" AND ") == 1
    assert "$3" in conditions[0] and "$4" in conditions[0]
    assert "$5" in conditions[1]
    for col in ("CAST(time AS TEXT)", "name", "levelname", "message"):
        assert f"{col} ILIKE $5" in conditions[1]


def test_keyword_conditions_skip_blank_items():
    conditions, params, nxt = PostgreSQL._build_keyword_conditions(["", "   "], 7)

    assert (conditions, params, nxt) == ([], [], 7)


def test_keyword_values_are_parameters_not_sql():
    conditions, params, _ = PostgreSQL._build_keyword_conditions(["'; DROP TABLE x; --"], 1)

    assert "DROP" not in " ".join(conditions)
    assert params == ["%';%", "%DROP%", "%TABLE%", "%x;%", "%--%"]


def test_fetch_conditions_minimal():
    conditions, params, nxt = PostgreSQL._build_fetch_conditions(T0, T1, None, "DESC", None, None)

    assert conditions == ["time BETWEEN $1 AND $2"]
    assert params == [T0, T1]
    assert nxt == 3


@pytest.mark.parametrize(("direction", "op"), [("DESC", "<"), ("ASC", ">")])
def test_fetch_conditions_cursor_direction(direction, op):
    cursor = T0 + timedelta(hours=1)
    conditions, params, nxt = PostgreSQL._build_fetch_conditions(T0, T1, cursor, direction, None, None)

    assert conditions[1] == f"time {op} $3"
    assert params[2] == cursor
    assert nxt == 4


def test_fetch_conditions_all_filters_number_placeholders_sequentially():
    cursor = T0 + timedelta(hours=1)
    conditions, params, nxt = PostgreSQL._build_fetch_conditions(
        T0, T1, cursor, "DESC", ["ERROR", "WARNING"], ["robot", "lamp on"],
    )

    assert conditions[:3] == ["time BETWEEN $1 AND $2", "time < $3", "levelname = ANY($4)"]
    assert conditions[3].startswith("((") and " OR " in conditions[3]
    assert params == [T0, T1, cursor, ["ERROR", "WARNING"], "%robot%", "%lamp%", "%on%"]
    assert nxt == 8


def test_fetch_conditions_blank_keywords_add_no_clause():
    conditions, params, nxt = PostgreSQL._build_fetch_conditions(T0, T1, None, "DESC", None, ["  "])

    assert conditions == ["time BETWEEN $1 AND $2"]
    assert nxt == 3


# --- fetch -------------------------------------------------------------------

async def test_fetch_builds_parameterized_query_with_limit(pg):
    await pg.fetch(T0, T1, row_count=50, levelnames=["INFO"])

    query, *params = pg._pool.fetch.await_args.args
    sql = _sql(query)
    assert sql.startswith("SELECT time, name, levelname, message FROM freedom.freedom_log")
    assert "WHERE time BETWEEN $1 AND $2 AND levelname = ANY($3)" in sql
    assert sql.endswith("ORDER BY time DESC LIMIT $4;")
    assert params == [T0, T1, ["INFO"], 50]


@pytest.mark.parametrize("row_count", [None, "null"])
async def test_fetch_without_limit(pg, row_count):
    await pg.fetch(T0, T1, row_count=row_count)

    query, *params = pg._pool.fetch.await_args.args
    assert "LIMIT" not in query
    assert params == [T0, T1]


@pytest.mark.parametrize(("field", "direction", "expected"), [
    ("name", "asc", "ORDER BY name ASC"),
    ("levelname", "ASC", "ORDER BY levelname ASC"),
    ("message", "desc", "ORDER BY message DESC"),
    ("time; DROP TABLE freedom_log", "asc", "ORDER BY time ASC"),
    ("name", "sideways", "ORDER BY name DESC"),
])
async def test_fetch_sort_is_whitelisted(pg, field, direction, expected):
    await pg.fetch(T0, T1, sort_field=field, sort_direction=direction)

    sql = _sql(pg._pool.fetch.await_args.args[0])
    assert expected in sql
    assert "DROP" not in sql


async def test_fetch_converts_rows_to_utc_columns(pg):
    jst = timezone(timedelta(hours=9))
    pg._pool.fetch.return_value = [
        {"time": datetime(2026, 1, 1, 9, 0, tzinfo=jst), "name": "n", "levelname": "INFO", "message": "m"},
    ]

    ret = await pg.fetch(T0, T1)

    assert ret == [Column(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc), "n", "INFO", "m")]
    assert ret[0].time.utcoffset() == timedelta(0)


# --- insert / partitions -----------------------------------------------------

async def test_insert_batches_rows_with_executemany(pg):
    pg._last_time = datetime(2026, 1, 5)
    logs = [
        Column(datetime(2026, 1, 5, 1), "a", "INFO", "x"),
        Column(datetime(2026, 1, 5, 2), "b", "ERROR", "y"),
    ]

    await pg.insert(logs)

    query, rows = pg._pool.executemany.await_args.args
    assert _sql(query) == "INSERT INTO freedom.freedom_log VALUES ($1, $2, $3, $4);"
    assert rows == [(logs[0].time, "a", "INFO", "x"), (logs[1].time, "b", "ERROR", "y")]
    pg._pool.execute.assert_not_awaited()


async def test_insert_creates_partition_once_per_new_day_and_prunes(pg):
    pg._last_time = datetime(2026, 1, 1)
    pg._pool.fetch.return_value = [
        {"tablename": "freedom_log_2025_12_30"},
        {"tablename": "freedom_log_2025_12_31"},
        {"tablename": "freedom_log_2026_01_01"},
        {"tablename": "freedom_log_2026_01_02"},
    ]
    logs = [
        Column(datetime(2026, 1, 2, 1), "a", "INFO", "x"),
        Column(datetime(2026, 1, 2, 2), "a", "INFO", "y"),
    ]

    await pg.insert(logs)

    executed = [_sql(call.args[0]) for call in pg._pool.execute.await_args_list]
    creates = [s for s in executed if s.startswith("CREATE TABLE")]
    drops = [s for s in executed if s.startswith("DROP TABLE")]
    assert len(creates) == 1
    assert "freedom.freedom_log_2026_01_02 PARTITION OF freedom.freedom_log" in creates[0]
    assert "FROM ('2026-01-02 00:00:00+0000') TO ('2026-01-03 00:00:00+0000')" in creates[0]
    # retention_period=2 keeps the newest two partitions
    assert drops == [
        "DROP TABLE IF EXISTS freedom.freedom_log_2025_12_30 CASCADE;",
        "DROP TABLE IF EXISTS freedom.freedom_log_2025_12_31 CASCADE;",
    ]
    assert pg._last_time == logs[0].time
    pg._pool.executemany.assert_awaited_once()
