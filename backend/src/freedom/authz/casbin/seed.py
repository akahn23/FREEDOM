# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import asyncpg
import csv
import io
from importlib import resources


def _read_policy_seed_csv() -> str:
    return (resources.files("src.freedom.authz.casbin") / "policy.seed.csv").read_text(encoding="utf-8")


async def seed_policy_if_empty(conn: asyncpg.Connection) -> bool:
    """
    Run policy.seed.csv if authz.casbin_rule is empty
    Skip if a policy already exists
    """
    count = await conn.fetchval("SELECT COUNT(*) FROM authz.casbin_rule;")
    if count and int(count) > 0:
        return False
    text = _read_policy_seed_csv()
    reader = csv.reader(io.StringIO(text))
    rows = []
    for row in reader:
        if not row:
            continue
        head = row[0].strip().lstrip("\ufeff")
        if not head or head.startswith("#"):
            continue
        ptype = head
        v0 = row[1].strip() if len(row) > 1 else None
        v1 = row[2].strip() if len(row) > 2 else None
        v2 = row[3].strip() if len(row) > 3 else None
        v3 = row[4].strip() if len(row) > 4 else None
        v4 = row[5].strip() if len(row) > 5 else None
        v5 = row[6].strip() if len(row) > 6 else None
        rows.append((ptype, v0, v1, v2, v3, v4, v5))
    if not rows:
        return True

    async with conn.transaction():
        await conn.executemany(
            """
            INSERT INTO authz.casbin_rule(ptype, v0, v1, v2, v3, v4, v5)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            """,
            rows,
        )
    return True
