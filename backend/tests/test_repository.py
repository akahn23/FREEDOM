import dataclasses

from src.repository import Repository


@dataclasses.dataclass
class FakeDomain:
    id: str = ""
    group: str = ""


class Base:
    def __init__(self, **domain):
        self.domain = FakeDomain(**domain)


class Child(Base):
    pass


class Other:
    def __init__(self, **domain):
        self.domain = FakeDomain(**domain)


def test_retrieve_returns_instances_and_subclasses_in_order():
    a, b, c = Base(id="a"), Child(id="b"), Other(id="c")
    repo = Repository([a, b, c])

    assert repo.retrieve(Base) == [a, b]
    assert repo.retrieve(Child) == [b]
    assert repo.retrieve(Other) == [c]


def test_retrieve_returns_empty_list_when_nothing_matches():
    repo = Repository([Other()])

    assert repo.retrieve(Base) == []
    assert Repository().retrieve(Base) == []


def test_retrieve_filters_on_domain_attributes():
    a = Base(id="a", group="robot")
    b = Base(id="b", group="robot")
    c = Base(id="c", group="equipment")
    repo = Repository([a, b, c])

    assert repo.retrieve(Base, group="robot") == [a, b]
    assert repo.retrieve(Base, id="b", group="robot") == [b]
    assert repo.retrieve(Base, id="b", group="equipment") == []


def test_retrieve_unknown_domain_attribute_only_matches_none():
    a = Base(id="a")
    repo = Repository([a])

    assert repo.retrieve(Base, missing="x") == []
    assert repo.retrieve(Base, missing=None) == [a]


def test_retrieve_without_kwargs_does_not_touch_domain():
    class NoDomain:
        pass

    item = NoDomain()
    assert Repository([item]).retrieve(NoDomain) == [item]


def test_retrieve_recurses_into_nested_repositories():
    a, b, c = Base(id="a"), Base(id="b"), Base(id="c")
    inner = Repository([b, Repository([c])])
    repo = Repository([a, inner])

    assert repo.retrieve(Base) == [a, b, c]
    assert repo.retrieve(Base, id="c") == [c]


def test_retrieve_repository_type_returns_nested_repository_itself():
    inner = Repository([Base()])
    repo = Repository([inner])

    assert repo.retrieve(Repository) == [inner]


def test_repository_behaves_like_a_list():
    repo = Repository()
    a = Base()
    repo.append(a)

    assert len(repo) == 1
    assert repo[0] is a
    assert repo.data == [a]
