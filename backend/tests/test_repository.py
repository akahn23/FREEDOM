import dataclasses
from unittest import mock

import pytest

import src.repository as repository_module
from src.repository import Repository


@dataclasses.dataclass
class Domain:
    name: str
    group: str = "robot"


class Node:
    def __init__(self, name, **domain_kwargs):
        self.domain = Domain(name=name, **domain_kwargs)

    def __repr__(self):
        return f"{type(self).__name__}({self.domain.name})"


class RobotNode(Node):
    pass


class LampNode(Node):
    pass


class SubRepository(Repository):
    pass


def test_module_level_repository_is_empty_repository():
    assert isinstance(repository_module.repository, Repository)
    assert list(repository_module.repository) == []


def test_behaves_like_list():
    r = Repository([1, 2])
    r.append(3)
    assert r.data == [1, 2, 3]
    assert len(r) == 3 and r[0] == 1
    r.remove(2)
    assert list(r) == [1, 3]


def test_retrieve_by_exact_type():
    a, b = RobotNode("a"), LampNode("b")
    r = Repository([a, b])
    assert r.retrieve(RobotNode) == [a]
    assert r.retrieve(LampNode) == [b]


def test_retrieve_includes_subclasses_in_order():
    a, b, c = RobotNode("a"), Node("b"), LampNode("c")
    r = Repository([a, b, c])
    assert r.retrieve(Node) == [a, b, c]


def test_retrieve_no_match_returns_empty_list():
    r = Repository([RobotNode("a")])
    assert r.retrieve(LampNode) == []
    assert Repository().retrieve(Node) == []


def test_retrieve_returns_new_list():
    a = RobotNode("a")
    r = Repository([a])
    found = r.retrieve(RobotNode)
    found.clear()
    assert r.retrieve(RobotNode) == [a]


def test_retrieve_searches_nested_repositories_recursively():
    a, b, c, d = RobotNode("a"), RobotNode("b"), LampNode("c"), RobotNode("d")
    inner = SubRepository([b, c, Repository([d])])
    r = Repository([a, inner])
    assert r.retrieve(RobotNode) == [a, b, d]
    assert r.retrieve(LampNode) == [c]


def test_retrieve_repository_type_returns_nested_repository_itself():
    inner = SubRepository([RobotNode("a")])
    r = Repository([inner])
    assert r.retrieve(SubRepository) == [inner]


def test_retrieve_filters_by_domain_kwargs():
    a = RobotNode("a", group="robot")
    b = RobotNode("b", group="robot")
    c = RobotNode("c", group="equipment")
    r = Repository([a, Repository([b, c])])
    assert r.retrieve(RobotNode, name="b") == [b]
    assert r.retrieve(RobotNode, group="robot") == [a, b]
    assert r.retrieve(RobotNode, group="equipment", name="c") == [c]
    assert r.retrieve(RobotNode, group="equipment", name="a") == []


def test_retrieve_unknown_domain_attribute_does_not_match():
    r = Repository([RobotNode("a")])
    assert r.retrieve(RobotNode, missing="x") == []


def test_retrieve_unknown_domain_attribute_matches_none():
    # getattr(..., None) default means a None filter matches any missing attribute.
    a = RobotNode("a")
    assert Repository([a]).retrieve(RobotNode, missing=None) == [a]


def test_retrieve_with_mocked_nodes():
    node = mock.Mock(spec=["domain"])
    node.domain = mock.Mock(name="domain", spec=["name"])
    node.domain.name = "mocked"
    r = Repository([node, Node("x")])
    assert r.retrieve(mock.Mock, name="mocked") == [node]
    assert r.retrieve(mock.Mock, name="other") == []


def test_retrieve_without_kwargs_does_not_require_domain():
    class Bare:
        pass

    item = Bare()
    assert Repository([item]).retrieve(Bare) == [item]


def test_retrieve_with_kwargs_on_item_without_domain_raises():
    # Documents current behaviour: items matching cls must expose .domain when filtering.
    class Bare:
        pass

    with pytest.raises(AttributeError):
        Repository([Bare()]).retrieve(Bare, name="x")


def test_global_repository_can_be_patched():
    a = RobotNode("a")
    with mock.patch.object(repository_module, "repository", Repository([a])):
        assert repository_module.repository.retrieve(RobotNode) == [a]
    assert repository_module.repository.retrieve(RobotNode) == []
