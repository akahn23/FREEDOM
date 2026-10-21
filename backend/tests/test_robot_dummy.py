import asyncio
import dataclasses
import logging
import types
from unittest.mock import MagicMock

import pytest
from src import equipment, freedom, infrastructure, job, robot, util  # noqa: F401
from src.job.active import Variable
from src.repository import repository
from src.robot import dummy
from src.robot.dummy import repository as dummy_repository_module

State = util.status.State
ACTIVE_SUFFIX = " \u5b9f\u884c\u4e2d"


@pytest.fixture
def log_node():
    node = object.__new__(freedom.log.Node)
    node.make_logger = MagicMock(side_effect=lambda name, prefix=None: logging.getLogger(f"tests.{name}"))
    repository.append(node)
    yield node
    repository.remove(node)


@pytest.fixture
def clean_repository():
    before = list(repository)
    yield
    repository[:] = before


def make_job(name="job", variables=(), error_msg=(), warning_msg=()):
    node = object.__new__(job.active.Node)
    node.domain = types.SimpleNamespace(
        id=name, name=name, variables=list(variables),
        error_msg=set(error_msg), warning_msg=set(warning_msg),
    )
    return node


def bare_node(name="r1", **kwargs):
    node = object.__new__(dummy.Node)
    node.domain = dummy.NodeDomain(name=name, **kwargs)
    node.job = None
    return node


# ---------------------------------------------------------------- domain

def test_node_domain_defaults_and_runtime_location():
    domain = dummy.NodeDomain()
    assert (domain.enable, domain.name, domain.update_cycle) == (True, "", 1.0)
    assert domain.location is None
    assert dataclasses.asdict(domain) == {"enable": True, "name": "", "update_cycle": 1.0}


def test_node_domain_form_matches_fields():
    form = dummy.NodeDomain.make_form()
    assert set(form) == {f.name for f in dataclasses.fields(dummy.NodeDomain)}
    assert form["update_cycle"]["type"] == "number"
    assert form["update_cycle"]["min"] == 0


def test_node_domain_equality_ignores_location():
    a = dummy.NodeDomain(name="r1")
    b = dummy.NodeDomain(name="r1")
    b.location = [1.0, 2.0]
    assert a == b
    assert a != dummy.NodeDomain(name="r1", update_cycle=2.0)


def test_domain_keeps_only_enabled_nodes():
    domain = dummy.Domain(node_domain=[
        {"enable": True, "name": "a", "update_cycle": 0.5},
        {"enable": False, "name": "b"},
        {"name": "missing-enable-flag"},
        {"enable": True, "name": "c"},
    ])
    assert [d.name for d in domain.node_domain] == ["a", "c"]
    assert all(isinstance(d, dummy.NodeDomain) for d in domain.node_domain)
    assert domain.node_domain[0].update_cycle == 0.5


def test_domain_default_is_empty_and_independent():
    first, second = dummy.Domain(), dummy.Domain()
    assert first.node_domain == [] and first.node_domain is not second.node_domain


def test_domain_form_describes_node_list():
    form = dummy.Domain.make_form()["node_domain"]
    assert form["type"] == "node"
    assert form["unique"] == ["name"]
    assert form["default"] == dataclasses.asdict(dummy.NodeDomain())
    assert form["forms"] == dummy.NodeDomain.make_form()


def test_domain_round_trips_through_asdict():
    original = dummy.Domain(node_domain=[{"enable": True, "name": "a", "update_cycle": 2.0}])
    restored = dummy.Domain(**dataclasses.asdict(original))
    assert restored.node_domain == original.node_domain


# ---------------------------------------------------------- fetch_status

def test_fetch_status_waiting_without_job():
    node = bare_node(name="r1")
    node.domain.location = [35.0, 137.0]
    status = node.fetch_status()
    assert status == util.status.Status(name="r1", state=State.WAITING, location=[35.0, 137.0], info=[])


def test_fetch_status_active_with_job():
    node = bare_node()
    node.job = make_job(name="deliver")
    status = node.fetch_status()
    assert status.state == State.ACTIVE
    assert status.info == ["deliver" + ACTIVE_SUFFIX]


def test_fetch_status_warning_lists_messages():
    node = bare_node()
    node.job = make_job(warning_msg={"low battery"})
    status = node.fetch_status()
    assert (status.state, status.info) == (State.WARNING, ["low battery"])


def test_fetch_status_error_takes_precedence_over_warning():
    node = bare_node()
    node.job = make_job(error_msg={"e1", "e2"}, warning_msg={"w"})
    status = node.fetch_status()
    assert status.state == State.ERROR
    assert sorted(status.info) == ["e1", "e2"]


# ---------------------------------------------------------------- update

def test_update_binds_job_that_references_robot(clean_repository):
    node = bare_node(name="r1")
    other = make_job("other", [Variable(id="v", name="v", type="Robot", value="r2")])
    mine = make_job("mine", [Variable(id="v", name="v", type="Robot", value="r1")])
    text_var = make_job("text", [Variable(id="v", name="v", type="String", value="r1")])
    repository.extend([other, text_var, mine])
    asyncio.run(node._update())
    assert node.job is mine


def test_update_clears_job_when_no_longer_referenced(clean_repository):
    node = bare_node(name="r1")
    node.job = make_job("stale")
    repository.append(make_job("other", [Variable(id="v", name="v", type="Robot", value="r9")]))
    asyncio.run(node._update())
    assert node.job is None


# --------------------------------------------------------- node lifecycle

def test_node_init_uses_log_node_and_loop_updates_job(log_node, clean_repository):
    job_node = make_job("mine", [Variable(id="v", name="v", type="Robot", value="r1")])
    repository.append(job_node)

    async def run():
        node = dummy.Node(dummy.NodeDomain(name="r1", update_cycle=0))
        assert node.job is None
        for _ in range(5):
            await asyncio.sleep(0)
        bound = node.job
        node._task.cancel()
        await asyncio.wait_for(node._task, 1)
        return node, bound

    node, bound = asyncio.run(run())
    log_node.make_logger.assert_called_once_with("src.robot.dummy", "[r1]")
    assert bound is job_node
    assert node._task.done() and not node._task.cancelled()


def test_node_loop_logs_close_on_cancel(log_node, clean_repository):
    async def run():
        node = dummy.Node(dummy.NodeDomain(name="r1", update_cycle=10))
        node._logger = MagicMock()
        await asyncio.sleep(0)
        node._task.cancel()
        await node._task
        return node

    node = asyncio.run(run())
    node._logger.info.assert_called_with("close")


# ------------------------------------------------------------ repository

class FakeNode:
    def __init__(self, domain):
        self.domain = domain
        self.closed = False

    def close(self):
        self.closed = True


def nodes_config(*names, cycle=1.0):
    return {"node_domain": [{"enable": True, "name": n, "update_cycle": cycle} for n in names]}


def registered():
    found = repository.retrieve(dummy.Repository)
    assert len(found) == 1
    return found[0]


@pytest.fixture
def fake_nodes(monkeypatch, clean_repository):
    monkeypatch.setattr(dummy_repository_module, "Node", FakeNode)


def test_repository_registers_once_and_creates_nodes(fake_nodes):
    dummy.Repository(nodes_config("a", "b"))
    repo = registered()
    assert [n.domain.name for n in repo] == ["a", "b"]
    assert all(isinstance(n, FakeNode) for n in repo)
    assert repo.domain.node_domain == [n.domain for n in repo]


def test_repository_reorders_keeps_and_removes_nodes(fake_nodes):
    dummy.Repository(nodes_config("a", "b", "c"))
    repo = registered()
    a, b, c = list(repo)
    dummy.Repository(nodes_config("c", "a", "d"))
    assert registered() is repo
    assert [n.domain.name for n in repo] == ["c", "a", "d"]
    assert repo[0] is c and repo[1] is a
    assert b.closed and not a.closed and not c.closed
    assert [d.name for d in repo.domain.node_domain] == ["c", "a", "d"]


def test_repository_replaces_node_when_settings_change(fake_nodes):
    dummy.Repository(nodes_config("a"))
    old = registered()[0]
    dummy.Repository(nodes_config("a", cycle=0.2))
    new = registered()[0]
    assert old.closed and new is not old
    assert new.domain.update_cycle == 0.2


def test_repository_disabling_node_removes_it(fake_nodes):
    dummy.Repository(nodes_config("a", "b"))
    config = nodes_config("a", "b")
    config["node_domain"][0]["enable"] = False
    dummy.Repository(config)
    assert [n.domain.name for n in registered()] == ["b"]


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=(
    "BUG: robot.dummy.Repository calls node.close() when a node is removed, "
    "but robot.dummy.Node (and robot.Node) define no close(), so removing a dummy robot crashes"))
def test_repository_removes_real_dummy_node(log_node, clean_repository):
    async def run():
        dummy.Repository(nodes_config("a", cycle=0))
        await asyncio.sleep(0)
        dummy.Repository(nodes_config())
        assert len(registered()) == 0
    asyncio.run(run())
