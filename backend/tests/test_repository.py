from dataclasses import dataclass

import pytest

from src.repository import Repository


@dataclass
class StubDomain:
    id: str
    group: str = 'robot'


@dataclass
class OtherDomain:
    id: str


class StubNode:
    def __init__(self, domain):
        self.domain = domain

    def __repr__(self):
        return f'{type(self).__name__}({self.domain!r})'


class SubStubNode(StubNode):
    pass


class UnrelatedNode:
    def __init__(self, domain):
        self.domain = domain


class StubRepository(Repository):
    pass


def node(id, group='robot', cls=StubNode):
    return cls(StubDomain(id=id, group=group))


def test_is_a_list():
    a = node('a')
    repo = Repository([a])
    assert list(repo) == [a]
    assert len(repo) == 1


def test_exact_type_match():
    a, b = node('a'), node('b')
    repo = Repository([a, UnrelatedNode(StubDomain('x')), b])
    assert repo.retrieve(StubNode) == [a, b]


def test_returns_plain_list():
    repo = Repository([node('a')])
    result = repo.retrieve(StubNode)
    assert type(result) is list


def test_subclass_instances_returned_for_base_class():
    base = node('base')
    sub = node('sub', cls=SubStubNode)
    repo = Repository([base, sub])
    assert repo.retrieve(StubNode) == [base, sub]


def test_base_instances_not_returned_for_subclass():
    base = node('base')
    sub = node('sub', cls=SubStubNode)
    repo = Repository([base, sub])
    assert repo.retrieve(SubStubNode) == [sub]


def test_tuple_of_classes():
    a = node('a')
    u = UnrelatedNode(StubDomain('u'))
    repo = Repository([a, u])
    assert repo.retrieve((StubNode, UnrelatedNode)) == [a, u]


def test_recurses_into_nested_repository():
    a, b = node('a'), node('b')
    repo = Repository([a, Repository([b])])
    assert repo.retrieve(StubNode) == [a, b]


def test_recurses_into_repository_subclass():
    a = node('a')
    repo = Repository([StubRepository([a])])
    assert repo.retrieve(StubNode) == [a]


def test_recurses_multiple_levels_deep():
    a, b, c, d = node('a'), node('b'), node('c'), node('d')
    repo = Repository([
        a,
        Repository([
            b,
            Repository([
                Repository([c]),
            ]),
        ]),
        d,
    ])
    assert repo.retrieve(StubNode) == [a, b, c, d]


def test_result_order_is_depth_first_in_insertion_order():
    n = {k: node(k) for k in 'abcdefg'}
    repo = Repository([
        Repository([n['a'], Repository([n['b'], n['c']])]),
        n['d'],
        Repository([Repository([n['e']]), n['f']]),
        n['g'],
    ])
    assert [x.domain.id for x in repo.retrieve(StubNode)] == list('abcdefg')


def test_nested_empty_repositories_contribute_nothing():
    a = node('a')
    repo = Repository([Repository(), Repository([Repository()]), a])
    assert repo.retrieve(StubNode) == [a]


def test_nested_repository_not_returned_as_item():
    inner = Repository([node('a')])
    repo = Repository([inner])
    assert inner not in repo.retrieve(StubNode)


def test_matching_repository_is_returned_and_not_recursed():
    inner = Repository([node('a')])
    repo = Repository([inner])
    assert repo.retrieve(Repository) == [inner]
    result = repo.retrieve(object)
    assert len(result) == 1
    assert result[0] is inner


def test_kwargs_single_filter():
    a = node('a', group='robot')
    b = node('b', group='equipment')
    c = node('c', group='robot')
    repo = Repository([a, b, c])
    assert repo.retrieve(StubNode, group='robot') == [a, c]


def test_kwargs_multiple_filters_all_must_match():
    a = node('a', group='robot')
    b = node('b', group='equipment')
    a2 = node('a', group='equipment')
    repo = Repository([a, b, a2])
    assert repo.retrieve(StubNode, id='a', group='equipment') == [a2]


def test_kwargs_filter_applies_in_nested_repositories():
    a = node('a', group='robot')
    b = node('b', group='equipment')
    c = node('c', group='robot')
    repo = Repository([a, Repository([b, Repository([c])])])
    assert repo.retrieve(StubNode, group='robot') == [a, c]


def test_kwargs_filter_combined_with_subclass():
    a = node('a', group='robot')
    sub = node('s', group='robot', cls=SubStubNode)
    other = node('o', group='infrastructure', cls=SubStubNode)
    repo = Repository([a, sub, other])
    assert repo.retrieve(SubStubNode, group='robot') == [sub]
    assert repo.retrieve(StubNode, group='robot') == [a, sub]


def test_non_matching_domain_excluded():
    a = node('a')
    repo = Repository([a, node('b')])
    assert repo.retrieve(StubNode, id='a') == [a]


def test_kwargs_unknown_attribute_excluded():
    repo = Repository([node('a')])
    assert repo.retrieve(StubNode, missing='x') == []


def test_kwargs_value_compared_by_equality():
    a = node('a')
    repo = Repository([a])
    assert repo.retrieve(StubNode, id='ab'[:1]) == [a]
    assert repo.retrieve(StubNode, domain=None) == [a]


def test_kwargs_none_matches_items_lacking_attribute():
    with_attr = StubNode(OtherDomain(id='x'))
    without_attr = node('y')
    repo = Repository([with_attr, without_attr])
    assert repo.retrieve(StubNode, extra=None) == [with_attr, without_attr]


def test_kwargs_none_matches_attribute_set_to_none():
    a = StubNode(StubDomain(id='a', group=None))
    b = node('b')
    repo = Repository([a, b])
    assert repo.retrieve(StubNode, group=None) == [a]


def test_no_kwargs_does_not_touch_domain():
    class NoDomain(StubNode):
        def __init__(self):
            pass

    item = NoDomain()
    repo = Repository([item])
    assert repo.retrieve(StubNode) == [item]


def test_kwargs_on_matching_item_without_domain_raises():
    class NoDomain(StubNode):
        def __init__(self):
            pass

    repo = Repository([NoDomain()])
    with pytest.raises(AttributeError):
        repo.retrieve(StubNode, id='a')


def test_empty_repository():
    assert Repository().retrieve(StubNode) == []
    assert Repository().retrieve(StubNode, id='a') == []


def test_no_type_match():
    repo = Repository([UnrelatedNode(StubDomain('a')), Repository([1, 'x'])])
    assert repo.retrieve(StubNode) == []


def test_no_kwargs_match():
    repo = Repository([node('a'), Repository([node('b')])])
    assert repo.retrieve(StubNode, id='z') == []


def test_retrieve_does_not_mutate_repository():
    a, b = node('a'), node('b')
    inner = Repository([b])
    repo = Repository([a, inner])
    repo.retrieve(StubNode, id='a')
    assert repo.data == [a, inner]
    assert inner.data == [b]
