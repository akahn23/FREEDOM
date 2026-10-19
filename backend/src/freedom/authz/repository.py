# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional

import asyncpg

SQL_GET_ROLE = """
SELECT role
FROM auth."user"
WHERE id = $1
"""

async def get_role_by_user_id(conn: asyncpg.Connection, user_id: str) -> Optional[str]:
    row = await conn.fetchrow(SQL_GET_ROLE, user_id)
    if not row:
        return None
    return row["role"]
