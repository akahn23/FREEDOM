# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
from datetime import datetime

from src.freedom.log import Column, Domain


class Interface(abc.ABC):
    @abc.abstractmethod
    def __init__(self, domain:Domain):
        """ログDB接続インターフェース
        Args:
            domain (Domain): 設定
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def insert(self, log_list:list[Column]):
        """ログ挿入
        Args:
            log_list (list[Column]): ログリスト
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def fetch(self, begin_time:datetime, end_time:datetime, row_count:int|None=None, cursor_time:datetime|None=None, keywords:list[str]|None=None, levelnames:list[str]|None=None, sort_field:str="time", sort_direction:str="desc") -> list[Column]:
        """ログ取得
        Args:
            begin_time (datetime): 開始日時
            end_time (datetime): 終了日時
            row_count (int|None): 取得件数 Noneで全取得
            cursor_time (datetime|None): 追加取得時に基準にする時刻
            keywords (list[str]|None): キーワード検索条件のリスト
            levelnames (list[str]|None): ログレベル
            sort_field (str): ソート対象カラム
            sort_direction (str): ソート順 (asc/desc)
        Returns:
            list[Column]: ログ
        """
        raise NotImplementedError()
