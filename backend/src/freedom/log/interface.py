# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
from datetime import datetime

from src.freedom.log import Domain, Column


class Interface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, domain:Domain):
        """Log database connection interface
        Args:
            domain (Domain): Settings
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def insert(self, log_list:list[Column]):
        """Insert logs
        Args:
            log_list (list[Column]): List of logs
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def fetch(self, begin_time:datetime, end_time:datetime, row_count:int|None=None, cursor_time:datetime|None=None, keywords:list[str]|None=None, levelnames:list[str]|None=None, sort_field:str="time", sort_direction:str="desc") -> list[Column]:
        """Get logs
        Args:
            begin_time (datetime): Start date/time
            end_time (datetime): End date/time
            row_count (int|None): Number of rows to fetch; None fetches all
            cursor_time (datetime|None): Reference time used when fetching additional rows
            keywords (list[str]|None): List of keyword search conditions
            levelnames (list[str]|None): Log levels
            sort_field (str): Column to sort by
            sort_direction (str): Sort order (asc/desc)
        Returns:
            list[Column]: Logs
        """
        raise NotImplementedError()
