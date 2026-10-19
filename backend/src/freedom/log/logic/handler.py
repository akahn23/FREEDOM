# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import datetime

from src.freedom.log import Column


class Handler(logging.Handler):
    def __init__(self, log_list:list[Column]):
        super().__init__()
        self._log_list = log_list

    def emit(self, record):
        self._log_list.append(Column(
            datetime.fromtimestamp(record.created),
            record.name,
            record.levelname,
            record.message
        ))
