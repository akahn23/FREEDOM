from types import SimpleNamespace

import pytest

from src.repository import Repository


class Base:
    def __init__(self, **domain):
        self.domain = SimpleNamespace(**domain)


class Robot(Base):
    pass


class Agv(Robot):
    pass


class Lamp(Base):
    pass


@pytest.fixture
def nodes():
    return {
        'robot': Robot(name='r1', group='robot', status=1),
        'agv': Agv(name='a1', group='robot', status=3),
        'lamp': Lamp(name='l1', group='infrastructure', status=1),
    }


@pytest.fixture
def repo(nodes):
    return Repository([nodes['robot'], nodes['agv'], nodes['lamp']])


def test_retrieve_by_exact_class(repo, nodes):
    assert repo.retrieve(Lamp) == [nodes['lamp']]
    assert repo.retrieve(Agv) == [nodes['agv']]


def test_retrieve_includes_subclasses(repo, nodes):
    assert repo.retrieve(Robot) == [nodes['robot'], nodes['agv']]
    assert repo.retrieve(Base) == [nodes['robot'], nodes['agv'], nodes['lamp']]


def test_retrieve_with_no_match_returns_empty_list(repo):
    class Other:
        pass
    assert repo.retrieve(Other) == []
    assert Repository().retrieve(Base) == []


def test_retrieve_preserves_insertion_order():
    a, b, c = Robot(name='c'), Robot(name='a'), Robot(name='b')
    assert Repository([a, b, c]).retrieve(Robot) == [a, b, c]


def test_filter_by_single_kwarg(repo, nodes):
    assert repo.retrieve(Base, status=1) == [nodes['robot'], nodes['lamp']]
    assert repo.retrieve(Robot, name='a1') == [nodes['agv']]


def test_filter_by_multiple_kwargs_requires_all(repo, nodes):
    assert repo.retrieve(Base, group='robot', status=1) == [nodes['robot']]
    assert repo.retrieve(Base, group='infrastructure', status=3) == []


def test_filter_with_no_matching_value(repo):
    assert repo.retrieve(Robot, name='l1') == []


def test_filter_on_missing_attribute_treated_as_none(repo, nodes):
    assert repo.retrieve(Base, missing='x') == []
    # getattr(..., None) default: a missing attribute matches None.
    assert repo.retrieve(Base, missing=None) == [nodes['robot'], nodes['agv'], nodes['lamp']]


def test_recurses_into_nested_repository(nodes):
    inner_agv = Agv(name='a2', group='robot', status=1)
    inner = Repository([inner_agv, Lamp(name='l2', status=1)])
    outer = Repository([nodes['robot'], inner, nodes['lamp']])
    assert outer.retrieve(Robot) == [nodes['robot'], inner_agv]
    assert outer.retrieve(Base, status=1) == [nodes['robot'], inner_agv, inner[1], nodes['lamp']]


def test_recurses_through_multiple_levels():
    deep = Lamp(name='deep')
    repo = Repository([Repository([Repository([deep])])])
    assert repo.retrieve(Lamp) == [deep]
    assert repo.retrieve(Lamp, name='deep') == [deep]
    assert repo.retrieve(Lamp, name='other') == []


def test_nested_repository_matching_cls_is_returned_not_searched():
    class NodeRepository(Repository):
        domain = SimpleNamespace(name='repo')

    child = Robot(name='child')
    nested = NodeRepository([child])
    outer = Repository([nested])
    # The nested repository itself matches the class, so it is returned and its items are not searched.
    assert outer.retrieve(Repository) == [nested]
    assert outer.retrieve(Robot) == [child]


def test_repository_behaves_like_list():
    repo = Repository()
    node = Robot(name='x')
    repo.append(node)
    assert len(repo) == 1
    assert repo.retrieve(Robot) == [node]
    repo.remove(node)
    assert repo.retrieve(Robot) == []
