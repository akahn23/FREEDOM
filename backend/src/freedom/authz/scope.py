# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncpg

"""ユーザごとの閲覧可能なノードを取得"""
SQL_ALLOW = """
SELECT node, node_id
FROM authz.user_node_allow
WHERE user_id = $1
"""

async def fetch_allow_set(conn: asyncpg.Connection, user_id: str) -> set[tuple[str, str]]:
    rows = await conn.fetch(SQL_ALLOW, user_id)
    return {(r["node"], r["node_id"]) for r in rows}
