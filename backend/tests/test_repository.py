import types

import pytest

from src import repository as repository_module
from src.repository import Repository


class Base:
    def __init__(self, **domain):
        self.domain = types.SimpleNamespace(**domain)

    def __repr__(self):
        return f"{type(self).__name__}({vars(self.domain)})"


class Child(Base):
    pass


class GrandChild(Child):
    pass


class Other(Base):
    pass


class NodeRepository(Repository):
    """Mirrors infrastructure.*.Repository: a Repository subclass with a domain."""
    def __init__(self, items=(), **domain):
        super().__init__(items)
        self.domain = types.SimpleNamespace(**domain)


def test_module_level_repository_is_an_empty_repository_instance():
    assert isinstance(repository_module.repository, Repository)


def test_repository_behaves_like_a_list():
    a, b = Base(name="a"), Base(name="b")
    repo = Repository([a])
    repo.append(b)
    assert list(repo) == [a, b]
    assert len(repo) == 2
    repo.remove(a)
    assert repo.data == [b]


def test_retrieve_empty_repository_returns_empty_list():
    assert Repository().retrieve(Base) == []


def test_retrieve_exact_class():
    a, o = Base(name="a"), Other(name="o")
    assert Repository([a, o]).retrieve(Other) == [o]


def test_retrieve_includes_subclasses_in_insertion_order():
    b, c, g, o = Base(), Child(), GrandChild(), Other()
    repo = Repository([g, o, b, c])
    assert repo.retrieve(Base) == [g, o, b, c]
    assert repo.retrieve(Child) == [g, c]
    assert repo.retrieve(GrandChild) == [g]


def test_retrieve_does_not_return_parent_class_instances_for_subclass_query():
    assert Repository([Base(), Other()]).retrieve(Child) == []


def test_retrieve_accepts_tuple_of_classes_like_isinstance():
    c, o, b = Child(), Other(), Base()
    assert Repository([c, o, b]).retrieve((Child, Other)) == [c, o]


def test_retrieve_returns_new_list_not_internal_data():
    a = Base()
    repo = Repository([a])
    result = repo.retrieve(Base)
    result.clear()
    assert repo.data == [a]


def test_retrieve_searches_nested_repositories():
    top, inner, deep = Child(name="top"), Child(name="inner"), Child(name="deep")
    repo = Repository([top, Repository([inner, Repository([deep])])])
    assert repo.retrieve(Child) == [top, inner, deep]


def test_retrieve_nested_results_are_flattened_in_depth_first_order():
    a, b, c, d = (Child(name=n) for n in "abcd")
    repo = Repository([a, Repository([b, Repository([c])]), d])
    assert [i.domain.name for i in repo.retrieve(Child)] == ["a", "b", "c", "d"]


def test_retrieve_nested_with_subclass_filtering():
    b, c, g, o = Base(), Child(), GrandChild(), Other()
    repo = Repository([b, Repository([o, Repository([g])]), Repository([c])])
    assert repo.retrieve(Child) == [g, c]
    assert repo.retrieve(Other) == [o]


def test_retrieve_repository_subclass_itself():
    lamp = NodeRepository([Child(name="lamp1")], name="lamp")
    repo = Repository([Base(), lamp])
    assert repo.retrieve(NodeRepository) == [lamp]


def test_matching_repository_is_returned_but_not_descended_into():
    inner = Child(name="inner")
    nested = NodeRepository([inner], name="repo")
    repo = Repository([nested])
    assert repo.retrieve(Repository) == [nested]


def test_retrieve_on_repository_subclass_children():
    lamp1, lamp2 = Child(name="lamp1"), Child(name="lamp2")
    repo = Repository([NodeRepository([lamp1, lamp2], name="lamp"), Other(name="x")])
    assert repo.retrieve(Child, name="lamp2") == [lamp2]


def test_retrieve_kwargs_filter_on_domain_attributes():
    a1 = Child(name="a", id=1)
    a2 = Child(name="a", id=2)
    b1 = Child(name="b", id=1)
    repo = Repository([a1, a2, b1])
    assert repo.retrieve(Child, name="a") == [a1, a2]
    assert repo.retrieve(Child, id=1) == [a1, b1]
    assert repo.retrieve(Child, name="a", id=2) == [a2]
    assert repo.retrieve(Child, name="c") == []


def test_retrieve_kwargs_filter_applies_inside_nested_repositories():
    a, b = Child(name="a"), Child(name="b")
    repo = Repository([Repository([a]), Repository([Repository([b])])])
    assert repo.retrieve(Child, name="b") == [b]


def test_retrieve_kwargs_combined_with_subclass_filter():
    c, g, o = Child(name="x"), GrandChild(name="x"), Other(name="x")
    repo = Repository([c, g, o])
    assert repo.retrieve(Child, name="x") == [c, g]


def test_retrieve_missing_domain_attribute_compares_as_none():
    item = Child(name="a")
    repo = Repository([item])
    assert repo.retrieve(Child, missing="value") == []
    assert repo.retrieve(Child, missing=None) == [item]


def test_retrieve_kwargs_on_repository_without_domain_raises():
    repo = Repository([Repository()])
    with pytest.raises(AttributeError):
        repo.retrieve(Repository, name="x")


def test_retrieve_repository_subclass_with_kwargs():
    lamp = NodeRepository(name="lamp")
    shutter = NodeRepository(name="shutter")
    repo = Repository([lamp, shutter])
    assert repo.retrieve(NodeRepository, name="shutter") == [shutter]


def test_repository_failing_kwargs_is_still_descended_into():
    inner = NodeRepository(name="target")
    outer = NodeRepository([inner], name="outer")
    assert Repository([outer]).retrieve(NodeRepository, name="target") == [inner]
