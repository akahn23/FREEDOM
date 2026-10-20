# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import inspect
import json

import pytest

from src import abstract, equipment, freedom, infrastructure, job, robot, util  # noqa: F401
from src.infrastructure import lamp


@dataclasses.dataclass
class SampleDomain(abstract.Domain):
    name: str = "sample"
    cycle: float = 1.0
    tags: list = dataclasses.field(default_factory=list)

    @classmethod
    def make_form(cls) -> dict:
        return {
            "name": {"type": "text", "label": "Name"},
            "cycle": {"type": "number", "label": "Cycle", "min": 0},
        }

    def __post_init__(self):
        super().__post_init__()
        self.runtime_counter = 0


def _concrete_domain_classes():
    def walk(cls):
        for sub in cls.__subclasses__():
            yield sub
            yield from walk(sub)
    classes = {c for c in walk(abstract.Domain) if not inspect.isabstract(c) and c.__module__.startswith("src.")}
    return sorted(classes, key=lambda c: f"{c.__module__}.{c.__qualname__}")


CONCRETE_DOMAINS = _concrete_domain_classes()


def _id(cls):
    return f"{cls.__module__.removeprefix('src.')}.{cls.__qualname__}"


def test_abstract_domain_cannot_be_instantiated():
    with pytest.raises(TypeError):
        abstract.Domain()


def test_subclass_without_make_form_cannot_be_instantiated():
    @dataclasses.dataclass
    class Incomplete(abstract.Domain):
        value: int = 0

    with pytest.raises(TypeError, match="make_form"):
        Incomplete()


def test_base_make_form_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        abstract.Domain.make_form()


def test_base_post_init_is_a_noop():
    assert abstract.Domain.__post_init__(SampleDomain()) is None


def test_domain_is_a_dataclass():
    assert dataclasses.is_dataclass(abstract.Domain)
    assert dataclasses.fields(abstract.Domain) == ()


def test_persistence_fields_are_dataclass_fields_only():
    domain = SampleDomain(name="lamp", cycle=2.5, tags=["a"])
    assert [f.name for f in dataclasses.fields(domain)] == ["name", "cycle", "tags"]
    assert dataclasses.asdict(domain) == {"name": "lamp", "cycle": 2.5, "tags": ["a"]}


def test_post_init_attributes_are_not_persisted_but_are_returned_to_ui():
    domain = SampleDomain()
    assert domain.runtime_counter == 0
    assert "runtime_counter" not in dataclasses.asdict(domain)
    # util.json.dumps (used for UI domain responses) serialises __dict__, so instance vars are included.
    assert json.loads(util.json.dumps(domain)) == {"name": "sample", "cycle": 1.0, "tags": [], "runtime_counter": 0}


def test_persisted_dict_round_trips_to_equal_domain():
    original = SampleDomain(name="x", cycle=3.0, tags=["t"])
    restored = SampleDomain(**dataclasses.asdict(original))
    assert restored == original
    assert restored.runtime_counter == 0


def test_mutable_defaults_are_not_shared():
    a, b = SampleDomain(), SampleDomain()
    a.tags.append("x")
    assert b.tags == []


def test_make_form_is_a_classmethod():
    assert SampleDomain.make_form() == SampleDomain().make_form()
    assert set(SampleDomain.make_form()) == {"name", "cycle"}


def test_infrastructure_make_form_covers_common_fields():
    form = infrastructure.Domain.make_form()
    assert set(form) == {"enable", "name", "location", "priority"}
    assert form["enable"]["type"] == "switch"
    assert form["location"]["type"] == "location"
    assert form["priority"]["integer"] is True


def test_lamp_node_make_form_extends_parent_form():
    form = lamp.NodeDomain.make_form()
    parent = infrastructure.Domain.make_form()
    assert parent.items() <= form.items()
    assert set(form) == {f.name for f in dataclasses.fields(lamp.NodeDomain)}
    assert "Dummy" in form["interface"]["items"]


def test_lamp_domain_make_form_nests_node_form_and_default():
    form = lamp.Domain.make_form()["node_domain"]
    assert form["type"] == "node"
    assert form["default"] == dataclasses.asdict(lamp.NodeDomain())
    assert form["forms"] == lamp.NodeDomain.make_form()
    assert form["unique"] == ["name"]


def test_lamp_domain_post_init_keeps_only_enabled_nodes_and_converts_areas():
    domain = lamp.Domain([
        {"enable": True, "name": "lamp_1", "area_list": [{"name": "a", "vertex_list": [[0, 0], [1, 0], [1, 1]]}]},
        {"enable": False, "name": "lamp_2"},
        {"name": "lamp_3"},
    ])
    assert [n.name for n in domain.node_domain] == ["lamp_1"]
    assert domain.node_domain[0].area_list == [util.map.Area("a", [[0, 0], [1, 0], [1, 1]])]


def test_lamp_domain_persistence_round_trip():
    original = lamp.Domain([{"enable": True, "name": "lamp_1", "ip": "10.0.0.1", "port": 502}])
    restored = lamp.Domain(**dataclasses.asdict(original))
    assert restored == original


def test_database_domain_defaults_to_dummy_without_main_node(clean_repository):
    domain = job.active.Domain()
    assert domain.interface == ""
    assert domain.table == "job_active"
    assert set(job.active.Domain.make_form()) == {"interface", "dsn", "schema", "table", "update_cycle"}
    assert set(job.active.Domain.make_form()["interface"]["items"]) == {"Dummy", "PostgreSQL"}


def test_database_domain_inherits_db_settings_from_main_node(clean_repository):
    main = object.__new__(freedom.main.Node)
    main.domain = freedom.main.Domain(interface="PostgreSQL", dsn="postgresql://u:p@h/db", schema="factory", table="freedom_main", update_cycle=10)
    clean_repository.append(main)
    domain = job.active.Domain()
    assert (domain.interface, domain.dsn, domain.schema) == ("PostgreSQL", "postgresql://u:p@h/db", "factory")
    assert domain.table == "job_active"


def test_database_domain_falls_back_to_dummy_for_unknown_main_interface(clean_repository):
    main = object.__new__(freedom.main.Node)
    main.domain = freedom.main.Domain(interface="Oracle", dsn="x", schema="s", table="t", update_cycle=10)
    clean_repository.append(main)
    domain = job.active.Domain()
    assert domain.interface == "Dummy"
    assert domain.dsn == ""


def test_database_domain_keeps_explicit_interface(clean_repository):
    main = object.__new__(freedom.main.Node)
    main.domain = freedom.main.Domain(interface="PostgreSQL", dsn="main-dsn", schema="s", table="t", update_cycle=10)
    clean_repository.append(main)
    domain = job.active.Domain(interface="Dummy", dsn="own-dsn")
    assert (domain.interface, domain.dsn) == ("Dummy", "own-dsn")


@pytest.mark.parametrize("cls", CONCRETE_DOMAINS, ids=_id)
def test_every_domain_form_only_references_persisted_fields(cls, clean_repository):
    fields = {f.name for f in dataclasses.fields(cls)}
    assert set(cls.make_form()) <= fields


@pytest.mark.parametrize("cls", CONCRETE_DOMAINS, ids=_id)
def test_every_domain_default_round_trips_through_asdict(cls, clean_repository):
    original = cls()
    assert cls(**dataclasses.asdict(original)) == original
    json.loads(util.json.dumps(dataclasses.asdict(original)))
