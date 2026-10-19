# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from casbin_async_sqlalchemy_adapter import create_casbin_rule_model
from sqlalchemy.orm import declarative_base

Base = declarative_base()

CasbinRule = create_casbin_rule_model(Base)

CasbinRule.__table__.schema = "authz"
