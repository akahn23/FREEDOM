import dataclasses

import repository


@dataclasses.dataclass
class FakeDomain:
    name: str
    kind: str = "default"


class Base:
    def __init__(self, name, kind="default"):
        self.domain = FakeDomain(name=name, kind=kind)


class Child(Base):
    pass


class Other:
    def __init__(self, name):
        self.domain = FakeDomain(name=name)


def test_retrieve_matches_class_and_subclasses():
    base, child, other = Base("a"), Child("b"), Other("c")
    repo = repository.Repository([base, child, other])

    assert repo.retrieve(Base) == [base, child]
    assert repo.retrieve(Child) == [child]
    assert repo.retrieve(Other) == [other]


def test_retrieve_filters_by_domain_kwargs():
    a = Base("a", kind="lamp")
    b = Base("b", kind="shutter")
    c = Child("c", kind="lamp")
    repo = repository.Repository([a, b, c])

    assert repo.retrieve(Base, kind="lamp") == [a, c]
    assert repo.retrieve(Base, name="b") == [b]
    assert repo.retrieve(Base, name="a", kind="shutter") == []
    assert repo.retrieve(Base, kind="gate") == []


def test_retrieve_recurses_into_nested_repository():
    outer_item = Base("outer", kind="lamp")
    inner_item = Child("inner", kind="lamp")
    inner_other = Other("inner_other")
    nested = repository.Repository([inner_item, inner_other])
    repo = repository.Repository([outer_item, nested])

    assert repo.retrieve(Base) == [outer_item, inner_item]
    assert repo.retrieve(Other) == [inner_other]
    assert repo.retrieve(Base, name="inner") == [inner_item]
