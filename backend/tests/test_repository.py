from dataclasses import dataclass

from src.repository import Repository


@dataclass
class FakeDomain:
    name: str
    kind: str = 'default'


class BaseNode:
    def __init__(self, name: str, kind: str = 'default') -> None:
        self.domain = FakeDomain(name=name, kind=kind)


class SubNode(BaseNode):
    pass


class OtherNode:
    def __init__(self, name: str) -> None:
        self.domain = FakeDomain(name=name)


def test_retrieve_exact_class_match():
    a = BaseNode('a')
    b = BaseNode('b')
    repo = Repository([a, OtherNode('x'), b])

    assert repo.retrieve(BaseNode) == [a, b]


def test_retrieve_includes_subclass_instances_for_base_class():
    base = BaseNode('base')
    sub = SubNode('sub')
    repo = Repository([base, sub, OtherNode('x')])

    assert repo.retrieve(BaseNode) == [base, sub]
    assert repo.retrieve(SubNode) == [sub]


def test_retrieve_filters_by_domain_attributes():
    a = BaseNode('a', kind='lamp')
    b = BaseNode('b', kind='lamp')
    c = BaseNode('a', kind='gate')
    repo = Repository([a, b, c])

    assert repo.retrieve(BaseNode, name='a') == [a, c]
    assert repo.retrieve(BaseNode, kind='lamp') == [a, b]
    assert repo.retrieve(BaseNode, name='a', kind='gate') == [c]


def test_retrieve_searches_nested_repositories():
    top = BaseNode('top')
    inner = SubNode('inner')
    deep = BaseNode('deep')
    repo = Repository([
        top,
        Repository([OtherNode('x'), inner, Repository([deep])]),
    ])

    assert repo.retrieve(BaseNode) == [top, inner, deep]
    assert repo.retrieve(BaseNode, name='deep') == [deep]
    assert repo.retrieve(OtherNode) == [repo[1][0]]


def test_retrieve_returns_empty_list_when_nothing_matches():
    repo = Repository([BaseNode('a'), Repository([SubNode('b')])])

    assert repo.retrieve(OtherNode) == []
    assert repo.retrieve(BaseNode, name='missing') == []
    assert repo.retrieve(BaseNode, kind='lamp') == []
    assert Repository().retrieve(BaseNode) == []
