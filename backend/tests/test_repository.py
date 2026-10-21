# SPDX-License-Identifier: Apache-2.0
"""Tests for src.repository: the in-memory node registry.

``Repository`` is a ``collections.UserList`` whose only custom method is
``retrieve(cls, **kwargs)``. Real nodes need a running event loop and a
database, so these tests use lightweight fake nodes that only carry a
``.domain`` namespace, mirroring how call sites query by ``id=`` / ``name=``
(e.g. ``repository.retrieve(job.active.Node, id=job_id)``).
"""

import types
from unittest import mock

import pytest

import src.repository
from src.repository import Repository


class BaseNode:
    """Fake node: real nodes expose their state on ``self.domain``."""

    def __init__(self, **domain):
        self.domain = types.SimpleNamespace(**domain)

    def __repr__(self):
        return f"{type(self).__name__}({vars(self.domain)})"


class LampNode(BaseNode):
    """Fake subclass node, e.g. infrastructure.lamp.Node."""


class RobotNode(BaseNode):
    """Fake sibling node unrelated to LampNode."""


class NoDomainNode:
    """Fake node that has no ``.domain`` attribute at all."""


class LampRepository(Repository[LampNode]):
    """Fake nested repository, like infrastructure.lamp.Repository."""


@pytest.fixture
def global_repository():
    """Snapshot and restore the module-level singleton around a test."""
    repo = src.repository.repository
    saved = list(repo.data)
    try:
        yield repo
    finally:
        repo.data[:] = saved


# --- Singleton -------------------------------------------------------------

def test_singleton_is_repository_instance():
    assert isinstance(src.repository.repository, Repository)
    assert isinstance(src.repository.repository, list) is False
    assert isinstance(src.repository.repository.data, list)


def test_singleton_append_retrieve_remove(global_repository):
    node = LampNode(id="lamp_1", name="Lamp 1")
    global_repository.append(node)
    assert global_repository.retrieve(LampNode, id="lamp_1") == [node]
    global_repository.remove(node)
    assert global_repository.retrieve(LampNode, id="lamp_1") == []


def test_singleton_shared_across_imports():
    from src.repository import repository as again
    assert again is src.repository.repository


# --- Create ----------------------------------------------------------------

def test_empty_construction():
    repo = Repository()
    assert len(repo) == 0
    assert list(repo) == []


def test_construct_from_iterable():
    a, b = LampNode(id="a"), LampNode(id="b")
    repo = Repository(iter([a, b]))
    assert list(repo) == [a, b]
    assert repo.data is not None and repo.data == [a, b]


def test_construct_from_repository_copies():
    a = LampNode(id="a")
    source = Repository([a])
    copy = Repository(source)
    copy.append(LampNode(id="b"))
    assert list(source) == [a]
    assert len(copy) == 2


def test_append_extend_insert():
    a, b, c, d = (LampNode(id=x) for x in "abcd")
    repo = Repository()
    repo.append(a)
    repo.extend([c, d])
    repo.insert(1, b)
    assert list(repo) == [a, b, c, d]
    assert repo.retrieve(LampNode) == [a, b, c, d]


def test_generic_typing_subscript():
    repo = Repository[int]([1, 2, 3])
    assert isinstance(repo, Repository)
    assert repo.retrieve(int) == [1, 2, 3]
    assert repo.retrieve(str) == []


def test_subclassing_generic_repository():
    repo = LampRepository([LampNode(id="a")])
    assert isinstance(repo, Repository)
    assert repo.retrieve(LampNode, id="a") == [repo[0]]


# --- Read ------------------------------------------------------------------

def test_retrieve_by_exact_class():
    lamp, robot = LampNode(id="l"), RobotNode(id="r")
    repo = Repository([lamp, robot])
    assert repo.retrieve(LampNode) == [lamp]
    assert repo.retrieve(RobotNode) == [robot]


def test_retrieve_by_base_class_includes_subclasses():
    base, lamp, robot = BaseNode(id="b"), LampNode(id="l"), RobotNode(id="r")
    repo = Repository([base, lamp, robot])
    assert repo.retrieve(BaseNode) == [base, lamp, robot]


def test_retrieve_subclass_excludes_base_instances():
    base, lamp = BaseNode(id="b"), LampNode(id="l")
    repo = Repository([base, lamp])
    assert repo.retrieve(LampNode) == [lamp]


def test_retrieve_tuple_of_classes():
    lamp, robot, other = LampNode(id="l"), RobotNode(id="r"), object()
    repo = Repository([lamp, other, robot])
    assert repo.retrieve((LampNode, RobotNode)) == [lamp, robot]


def test_retrieve_single_kwarg():
    a, b = LampNode(id="lamp_1"), LampNode(id="lamp_2")
    repo = Repository([a, b])
    assert repo.retrieve(LampNode, id="lamp_2") == [b]


def test_retrieve_multiple_kwargs_all_must_match():
    a = LampNode(id="lamp_1", name="North")
    b = LampNode(id="lamp_1", name="South")
    c = LampNode(id="lamp_2", name="North")
    repo = Repository([a, b, c])
    assert repo.retrieve(LampNode, id="lamp_1", name="North") == [a]
    assert repo.retrieve(LampNode, id="lamp_2", name="South") == []
    assert repo.retrieve(LampNode, name="North") == [a, c]


def test_retrieve_no_kwargs_returns_all_of_type():
    nodes = [LampNode(id=str(i)) for i in range(5)]
    repo = Repository(nodes)
    assert repo.retrieve(LampNode) == nodes


def test_retrieve_preserves_order():
    nodes = [LampNode(id=i, group="g") for i in (3, 1, 2)]
    repo = Repository([RobotNode(id=0), *nodes, RobotNode(id=9)])
    assert [n.domain.id for n in repo.retrieve(LampNode, group="g")] == [3, 1, 2]


def test_retrieve_returns_new_list_with_same_objects():
    a = LampNode(id="a")
    repo = Repository([a])
    result = repo.retrieve(LampNode)
    assert isinstance(result, list) and not isinstance(result, Repository)
    assert result[0] is a
    result.clear()
    assert list(repo) == [a]


def test_retrieve_returns_duplicates_if_stored_twice():
    a = LampNode(id="a")
    repo = Repository([a, a])
    assert repo.retrieve(LampNode, id="a") == [a, a]


def test_retrieve_recurses_into_nested_repository():
    inner_lamp = LampNode(id="inner")
    outer_robot = RobotNode(id="outer")
    repo = Repository([outer_robot, LampRepository([inner_lamp])])
    assert repo.retrieve(LampNode) == [inner_lamp]
    assert repo.retrieve(LampNode, id="inner") == [inner_lamp]
    assert repo.retrieve(BaseNode) == [outer_robot, inner_lamp]


def test_retrieve_nested_order_follows_position():
    first, nested, last = LampNode(id=1), LampNode(id=2), LampNode(id=3)
    repo = Repository([first, Repository([nested]), last])
    assert repo.retrieve(LampNode) == [first, nested, last]


def test_retrieve_multi_level_nesting():
    deep = LampNode(id="deep")
    mid = LampNode(id="mid")
    repo = Repository([Repository([mid, Repository([Repository([deep])])])])
    assert repo.retrieve(LampNode) == [mid, deep]
    assert repo.retrieve(LampNode, id="deep") == [deep]


def test_retrieve_empty_nested_repository():
    repo = Repository([Repository(), Repository([Repository()])])
    assert repo.retrieve(LampNode) == []


def test_nested_repository_matching_cls_is_returned_not_descended():
    """A nested repo that is itself an instance of cls is returned as a
    whole; its children are not searched (``elif`` branch is skipped)."""
    inner_lamp = LampNode(id="inner")
    nested = LampRepository([inner_lamp])
    repo = Repository([nested])
    assert repo.retrieve(LampRepository) == [nested]
    assert repo.retrieve(Repository) == [nested]
    assert repo.retrieve(object) == [nested]


def test_nested_repository_matching_cls_with_domain_filters_on_domain():
    """Real nested repositories (e.g. infrastructure.lamp.Repository) carry a
    ``.domain``; kwargs are then matched against that domain."""
    nested = LampRepository([LampNode(id="inner")])
    nested.domain = types.SimpleNamespace(name="lamps")
    repo = Repository([nested])
    assert repo.retrieve(LampRepository, name="lamps") == [nested]
    assert repo.retrieve(LampRepository, name="other") == []


def test_nested_repository_matching_cls_without_domain_raises_with_kwargs():
    """A plain nested Repository has no ``.domain``; filtering it by kwargs
    raises AttributeError rather than skipping or descending into it."""
    repo = Repository([LampRepository([LampNode(id="inner")])])
    with pytest.raises(AttributeError):
        repo.retrieve(LampRepository, id="inner")


def test_retrieve_is_case_and_type_sensitive():
    repo = Repository([LampNode(id=1, name="Lamp")])
    assert repo.retrieve(LampNode, name="lamp") == []
    assert repo.retrieve(LampNode, id="1") == []
    assert repo.retrieve(LampNode, id=1.0) == [repo[0]]


def test_retrieve_with_unittest_mock_nodes():
    node = mock.Mock(spec=BaseNode)
    node.domain = types.SimpleNamespace(id="job_1")
    repo = Repository([node])
    assert repo.retrieve(BaseNode, id="job_1") == [node]
    assert repo.retrieve(BaseNode, id="job_2") == []


def test_retrieve_mock_domain_auto_attributes_never_none():
    """A bare Mock domain auto-creates attributes, so a missing key yields a
    Mock (not None) and an equality filter on it does not match."""
    node = mock.Mock(spec=BaseNode)
    node.domain = mock.Mock()
    repo = Repository([node])
    assert repo.retrieve(BaseNode, id="x") == []
    assert repo.retrieve(BaseNode, id=None) == []


# --- Update ----------------------------------------------------------------

def test_mutating_domain_changes_retrieve_results():
    node = LampNode(id="lamp_1", status=0)
    repo = Repository([node])
    assert repo.retrieve(LampNode, status=3) == []
    node.domain.status = 3
    assert repo.retrieve(LampNode, status=3) == [node]
    assert repo.retrieve(LampNode, status=0) == []


def test_replacing_domain_object_changes_results():
    node = LampNode(id="old")
    repo = Repository([node])
    node.domain = types.SimpleNamespace(id="new")
    assert repo.retrieve(LampNode, id="old") == []
    assert repo.retrieve(LampNode, id="new") == [node]


def test_replace_item_by_index():
    old, new = LampNode(id="a"), RobotNode(id="a")
    repo = Repository([old])
    repo[0] = new
    assert repo.retrieve(LampNode) == []
    assert repo.retrieve(RobotNode, id="a") == [new]


def test_replace_slice():
    a, b, c = LampNode(id="a"), LampNode(id="b"), LampNode(id="c")
    repo = Repository([a, b])
    repo[0:2] = [c]
    assert list(repo) == [c]


def test_mutating_nested_repository_visible_from_parent():
    nested = Repository()
    repo = Repository([nested])
    node = LampNode(id="late")
    nested.append(node)
    assert repo.retrieve(LampNode, id="late") == [node]


# --- Delete ----------------------------------------------------------------

def test_remove_item():
    a, b = LampNode(id="a"), LampNode(id="b")
    repo = Repository([a, b])
    repo.remove(a)
    assert list(repo) == [b]
    assert repo.retrieve(LampNode, id="a") == []


def test_remove_retrieved_item_like_call_sites():
    """Mirrors freedom.map.Node: ``if old := retrieve(cls): remove(old[0])``."""
    old = LampNode(id="map")
    repo = Repository([RobotNode(id="r"), old])
    if found := repo.retrieve(LampNode):
        repo.remove(found[0])
    assert repo.retrieve(LampNode) == []
    assert len(repo) == 1


def test_remove_missing_item_raises_value_error():
    repo = Repository([LampNode(id="a")])
    with pytest.raises(ValueError):
        repo.remove(LampNode(id="a"))


def test_remove_from_empty_raises_value_error():
    with pytest.raises(ValueError):
        Repository().remove(object())


def test_remove_does_not_search_nested_repository():
    inner = LampNode(id="inner")
    repo = Repository([Repository([inner])])
    with pytest.raises(ValueError):
        repo.remove(inner)


def test_del_and_pop():
    a, b, c = LampNode(id="a"), LampNode(id="b"), LampNode(id="c")
    repo = Repository([a, b, c])
    del repo[0]
    assert repo.pop() is c
    assert list(repo) == [b]
    with pytest.raises(IndexError):
        Repository().pop()


def test_clear():
    repo = Repository([LampNode(id="a"), Repository([LampNode(id="b")])])
    repo.clear()
    assert len(repo) == 0
    assert repo.retrieve(LampNode) == []


# --- Not found / error handling ---------------------------------------------

def test_retrieve_on_empty_repository():
    assert Repository().retrieve(LampNode) == []
    assert Repository().retrieve(LampNode, id="x") == []


def test_retrieve_no_type_match():
    repo = Repository([RobotNode(id="r"), 1, "s", None])
    assert repo.retrieve(LampNode) == []


def test_retrieve_kwarg_value_mismatch():
    repo = Repository([LampNode(id="a")])
    assert repo.retrieve(LampNode, id="b") == []


def test_retrieve_missing_domain_attribute_does_not_match_value():
    repo = Repository([LampNode(id="a")])
    assert repo.retrieve(LampNode, name="x") == []


def test_retrieve_missing_domain_attribute_matches_none():
    """``getattr(domain, k, None)`` means ``attr=None`` matches items that
    lack the attribute as well as items whose attribute is None."""
    lacking = LampNode(id="a")
    explicit_none = LampNode(id="b", name=None)
    named = LampNode(id="c", name="x")
    repo = Repository([lacking, explicit_none, named])
    assert repo.retrieve(LampNode, name=None) == [lacking, explicit_none]


def test_item_without_domain_matches_when_no_kwargs():
    node = NoDomainNode()
    repo = Repository([node])
    assert repo.retrieve(NoDomainNode) == [node]
    assert repo.retrieve(object) == [node]


def test_item_without_domain_raises_attribute_error_with_kwargs():
    repo = Repository([NoDomainNode()])
    with pytest.raises(AttributeError):
        repo.retrieve(NoDomainNode, id="x")


def test_non_matching_item_without_domain_is_ignored_with_kwargs():
    lamp = LampNode(id="a")
    repo = Repository([NoDomainNode(), 42, lamp])
    assert repo.retrieve(LampNode, id="a") == [lamp]


def test_domain_none_treats_every_attribute_as_none():
    """getattr(None, k, None) is None, so a None domain never raises."""
    node = LampNode()
    node.domain = None
    repo = Repository([node])
    assert repo.retrieve(LampNode) == [node]
    assert repo.retrieve(LampNode, id=None) == [node]
    assert repo.retrieve(LampNode, id="x") == []


def test_retrieve_rejects_non_type_cls():
    repo = Repository([LampNode(id="a")])
    with pytest.raises(TypeError):
        repo.retrieve("LampNode")


def test_retrieve_on_empty_repo_accepts_any_cls():
    """With no items, ``isinstance`` is never called, so no TypeError."""
    assert Repository().retrieve("not a type") == []


def test_first_match_indexing_on_empty_result_raises_index_error():
    """Call sites use ``retrieve(...)[0]``; a miss surfaces as IndexError."""
    with pytest.raises(IndexError):
        Repository([RobotNode(id="r")]).retrieve(LampNode, id="x")[0]
