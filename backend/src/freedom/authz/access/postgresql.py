# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

"""AuthZ初期化用PostgreSQL定義
- authzスキーマ作成
- user_node_allow / user_node_deny / user_job_allow テーブル作成
- authz.casbin_ruleテーブル作成(Casbin policy保存先)
- index/unique 制約の整備
- policy.seed.csvの初回自動投入(casbin_rule が空なら)
"""

from src import abstract, freedom
from src.repository import repository
from src.freedom.authz.domain import Domain
from src.freedom.authz.interface import Interface
from src.freedom.authz.casbin.seed import seed_policy_if_empty


# Better Auth 用（schemaのみ作成。テーブル群はBetter Auth migrateで作成）
SQL_CREATE_AUTH_SCHEMA = "CREATE SCHEMA IF NOT EXISTS auth;"

# authz 用
SQL_CREATE_AUTHZ_SCHEMA = "CREATE SCHEMA IF NOT EXISTS authz;"

SQL_CREATE_USER_NODE_ALLOW = """
CREATE TABLE IF NOT EXISTS authz.user_node_allow (
  id bigserial PRIMARY KEY,
  user_id text NOT NULL,
  repository text NOT NULL,
  node text NOT NULL,
  node_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT NOW()
);
"""

SQL_CREATE_USER_NODE_DENY = """
CREATE TABLE IF NOT EXISTS authz.user_node_deny (
  id bigserial PRIMARY KEY,
  user_id text NOT NULL,
  repository text NOT NULL,
  node text NOT NULL,
  node_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT NOW()
);
"""

SQL_CREATE_USER_JOB_ALLOW = """
CREATE TABLE IF NOT EXISTS authz.user_job_allow (
  id bigserial PRIMARY KEY,
  user_id text NOT NULL,
  job_name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT NOW()
);
"""

SQL_CREATE_CASBIN_RULE = """
CREATE TABLE IF NOT EXISTS authz.casbin_rule (
  id bigserial PRIMARY KEY,
  ptype varchar(255) NOT NULL,
  v0 varchar(255),
  v1 varchar(255),
  v2 varchar(255),
  v3 varchar(255),
  v4 varchar(255),
  v5 varchar(255)
);
"""

SQL_CREATE_INDEXES = [
  "CREATE INDEX IF NOT EXISTS idx_user_node_allow_user ON authz.user_node_allow(user_id);",
  "CREATE INDEX IF NOT EXISTS idx_user_node_deny_user  ON authz.user_node_deny(user_id);",
  "CREATE INDEX IF NOT EXISTS idx_user_job_allow_user  ON authz.user_job_allow(user_id);",
  "CREATE INDEX IF NOT EXISTS idx_casbin_rule_ptype    ON authz.casbin_rule(ptype);",
  "CREATE INDEX IF NOT EXISTS idx_casbin_rule_v0       ON authz.casbin_rule(v0);",
]

SQL_ENSURE_CONSTRAINTS = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'authz'
      AND t.relname = 'user_node_allow'
      AND c.conname = 'user_node_allow_unique'
  ) THEN
    ALTER TABLE authz.user_node_allow
      ADD CONSTRAINT user_node_allow_unique
      UNIQUE (user_id, repository, node, node_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'authz'
      AND t.relname = 'user_node_deny'
      AND c.conname = 'user_node_deny_unique'
  ) THEN
    ALTER TABLE authz.user_node_deny
      ADD CONSTRAINT user_node_deny_unique
      UNIQUE (user_id, repository, node, node_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'authz'
      AND t.relname = 'user_job_allow'
      AND c.conname = 'user_job_allow_unique'
  ) THEN
    ALTER TABLE authz.user_job_allow
      ADD CONSTRAINT user_job_allow_unique
      UNIQUE (user_id, job_name);
  END IF;
END
$$;
"""


class PostgreSQL(abstract.access.PostgreSQL[Domain], Interface):
    def __init__(self, domain: Domain):
        """AuthZ PostgreSQL connection
        Args:
            domain (Domain): Settings
        """
        super().__init__(
            domain,
            repository.retrieve(freedom.log.Node)[0].make_logger(__name__),
        )

    async def _on_connect(self):
        """Post-connection event
        - Create the auth / authz schemas
        - Create authz tables/constraints/indexes
        - Seed the casbin policy (inserted if casbin_rule is empty)
        """
        await self._pool.execute(SQL_CREATE_AUTH_SCHEMA)
        await self._pool.execute(SQL_CREATE_AUTHZ_SCHEMA)
        await self._pool.execute(SQL_CREATE_USER_NODE_ALLOW)
        await self._pool.execute(SQL_CREATE_USER_NODE_DENY)
        await self._pool.execute(SQL_CREATE_USER_JOB_ALLOW)
        await self._pool.execute(SQL_CREATE_CASBIN_RULE)
        for q in SQL_CREATE_INDEXES:
            await self._pool.execute(q)
        await self._pool.execute(SQL_ENSURE_CONSTRAINTS)
        async with self._pool.acquire() as conn:
            await seed_policy_if_empty(conn)
