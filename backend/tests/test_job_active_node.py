import asyncio
import types
import unittest.mock

import pytest

from src import job
from src.job.active import node as node_module


def make_node(task_logic=None, error_msg=None):
    """__init__を通さずにノードを生成する (ロガー登録・タスク起動を回避)"""
    node = object.__new__(job.active.Node)
    node.domain = types.SimpleNamespace(
        id="1", name="job", error_msg=set(error_msg or ()), warning_msg=set(), variables=[],
    )
    node._logger = unittest.mock.Mock()
    node._task_logic = task_logic
    return node


def make_registry(*nodes):
    registry = object.__new__(job.active.Repository)
    registry.data = list(nodes)
    return registry


async def test_exec_command_dispatches_to_task():
    task = unittest.mock.Mock(exec_command=unittest.mock.AsyncMock(return_value="ok"))
    logic = unittest.mock.Mock(retrieve_task=unittest.mock.Mock(return_value=task))
    node = make_node(task_logic=logic)

    assert await node.exec_command("go", id="t1") == "ok"
    logic.retrieve_task.assert_called_once_with("t1")
    task.exec_command.assert_awaited_once_with("go")


async def test_exec_command_unknown_task_raises_clear_error():
    logic = unittest.mock.Mock(retrieve_task=unittest.mock.Mock(return_value=None))
    node = make_node(task_logic=logic)

    with pytest.raises(Exception, match="does not exist"):
        await node.exec_command("go", id="missing")


async def test_exec_command_when_task_logic_failed_to_build():
    node = make_node(task_logic=None, error_msg={"init failed"})

    with pytest.raises(Exception, match="Failed to exec_command") as excinfo:
        await node.exec_command("go", id="t1")
    assert not isinstance(excinfo.value, AttributeError)


def make_looping_node():
    """_loopを実行できるノード (タスクは完了しない)"""
    node = make_node()

    async def make_logic(job_id, logger):
        return unittest.mock.Mock(retrieve_task=unittest.mock.Mock(return_value=None))

    async def run_forever(logic, logger):
        await asyncio.Event().wait()

    node.domain.task = types.SimpleNamespace(make_logic=make_logic)
    node.domain.command = types.SimpleNamespace(exec=run_forever)
    return node


async def run_loop_and_cancel(node):
    loop_task = asyncio.create_task(node._loop())
    for _ in range(5):
        await asyncio.sleep(0)
    loop_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await loop_task


async def test_loop_cleanup_removes_node_from_registry(monkeypatch):
    node = make_looping_node()
    registry = make_registry(node)
    monkeypatch.setattr(node_module, "repository", make_registry(registry))

    await run_loop_and_cancel(node)

    assert node not in registry
    node._logger.info.assert_called_with("finish")


async def test_loop_cleanup_after_registry_replaced(monkeypatch):
    """設定更新で旧リポジトリが新リポジトリに置き換わった後でも終了処理が完了する"""
    node = make_looping_node()
    new_registry = make_registry()
    monkeypatch.setattr(node_module, "repository", make_registry(new_registry))

    await run_loop_and_cancel(node)

    node._logger.info.assert_called_with("finish")


async def test_loop_cleanup_without_registry(monkeypatch):
    node = make_looping_node()
    monkeypatch.setattr(node_module, "repository", make_registry())

    await run_loop_and_cancel(node)

    node._logger.info.assert_called_with("finish")
