# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

from src import repository as repository_module
from src.repository import Repository


class Base:
    def __init__(self, **domain):
        self.domain = SimpleNamespace(**domain)

    def __repr__(self):
        return f"{type(self).__name__}({vars(self.domain)})"


class Child(Base):
    pass


class GrandChild(Child):
    pass


class Other:
    def __init__(self, **domain):
        self.domain = SimpleNamespace(**domain)


def test_module_singleton_is_a_repository():
    assert isinstance(repository_module.repository, Repository)


def test_retrieve_on_empty_repository_returns_empty_list():
    assert Repository().retrieve(Base) == []


def test_retrieve_matches_exact_class():
    a, b = Base(name="a"), Other(name="b")
    repo = Repository([a, b])
    assert repo.retrieve(Base) == [a]
    assert repo.retrieve(Other) == [b]


def test_retrieve_includes_subclasses_in_insertion_order():
    base, child, grand, other = Base(), Child(), GrandChild(), Other()
    repo = Repository([child, other, grand, base])
    assert repo.retrieve(Base) == [child, grand, base]
    assert repo.retrieve(Child) == [child, grand]
    assert repo.retrieve(GrandChild) == [grand]


def test_retrieve_does_not_match_superclass_instances():
    repo = Repository([Base(), Other()])
    assert repo.retrieve(Child) == []


def test_retrieve_returns_plain_list_not_repository():
    result = Repository([Base()]).retrieve(Base)
    assert type(result) is list


def test_retrieve_recurses_into_nested_repositories_depth_first():
    a, b, c, d = Base(name="a"), Child(name="b"), Base(name="c"), Base(name="d")
    inner = Repository([b, Repository([c])])
    repo = Repository([a, inner, d])
    assert repo.retrieve(Base) == [a, b, c, d]


def test_retrieve_nested_repository_with_no_match():
    repo = Repository([Repository([Other()]), Repository()])
    assert repo.retrieve(Base) == []


def test_retrieve_repository_class_returns_top_level_repositories_without_recursing():
    deepest = Repository()
    middle = Repository([deepest])
    repo = Repository([middle, Base()])
    assert repo.retrieve(Repository) == [middle]


def test_retrieve_subclass_of_repository_matches_and_is_also_searched_by_parent_type():
    class JobRepository(Repository):
        pass

    job = Base(name="job")
    job_repo = JobRepository([job])
    repo = Repository([job_repo])
    assert repo.retrieve(JobRepository) == [job_repo]
    assert repo.retrieve(Base) == [job]


def test_retrieve_filters_on_domain_attributes():
    a1 = Base(name="a", id=1)
    a2 = Base(name="a", id=2)
    b1 = Base(name="b", id=1)
    repo = Repository([a1, a2, b1])
    assert repo.retrieve(Base, name="a") == [a1, a2]
    assert repo.retrieve(Base, id=1) == [a1, b1]
    assert repo.retrieve(Base, name="a", id=2) == [a2]
    assert repo.retrieve(Base, name="c") == []


def test_retrieve_filter_uses_equality_not_identity():
    node = Base(id="42")
    repo = Repository([node])
    assert repo.retrieve(Base, id="".join(["4", "2"])) == [node]
    assert repo.retrieve(Base, id=42) == []


def test_retrieve_filter_on_missing_attribute_compares_against_none():
    with_attr = Base(name="x", group="robot")
    without_attr = Base(name="y")
    repo = Repository([with_attr, without_attr])
    assert repo.retrieve(Base, group="robot") == [with_attr]
    assert repo.retrieve(Base, group=None) == [without_attr]


def test_retrieve_filter_applies_inside_nested_repositories():
    match = Child(name="target")
    repo = Repository([Base(name="other"), Repository([Child(name="nope"), match])])
    assert repo.retrieve(Base, name="target") == [match]
    assert repo.retrieve(Child, name="target") == [match]


def test_retrieve_without_filters_does_not_require_domain():
    class NoDomain:
        pass

    item = NoDomain()
    assert Repository([item]).retrieve(NoDomain) == [item]


def test_repository_behaves_like_a_list():
    repo = Repository([1, 2])
    repo.append(3)
    repo.remove(1)
    assert list(repo) == [2, 3]
    assert len(repo) == 2
    assert repo.retrieve(int) == [2, 3]
