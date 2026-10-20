# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import abc
import asyncio


def _current_task() -> asyncio.Task|None:
    try:
        return asyncio.current_task()
    except RuntimeError:
        return None


class Lifecycle(abc.ABC):
    """処理ループのライフサイクル管理
    start()でループタスクを起動し、shutdown()/aclose()で明示的に停止する
    Attributes:
        _task (asyncio.Task|None): ループタスク
        _stop_event (asyncio.Event|None): 停止要求
    """
    _task:asyncio.Task|None = None
    _stop_event:asyncio.Event|None = None

    @abc.abstractmethod
    async def _loop(self):
        """処理ループ
        self.runningがFalseになるか、キャンセルされたら終了すること
        """
        raise NotImplementedError("Subclasses must implement _loop method")

    @property
    def running(self) -> bool:
        """ループ稼働中 (停止要求なし)"""
        return self._task is not None and not self._task.done() and not self._stop_event.is_set()

    def start(self):
        """ループ起動 稼働中なら何もしない"""
        if self._task is not None and not self._task.done():
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._loop())

    def shutdown(self):
        """停止要求
        停止フラグを立ててループタスクをキャンセルする (完了は待たない)
        """
        if self._task is None:
            return
        self._stop_event.set()
        if not self._task.done() and self._task is not _current_task():
            self._task.cancel()

    async def aclose(self):
        """停止
        停止要求後、ループタスクの終了処理完了まで待つ
        """
        self.shutdown()
        if self._task is not None and self._task is not _current_task():
            await asyncio.wait([self._task])


def shutdown(obj):
    """Lifecycleであれば停止要求する
    Args:
        obj (typing.Any): 対象
    """
    if isinstance(obj, Lifecycle):
        obj.shutdown()


async def aclose(obj):
    """Lifecycleであれば停止完了まで待つ
    Args:
        obj (typing.Any): 対象
    """
    if isinstance(obj, Lifecycle):
        await obj.aclose()
