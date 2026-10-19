import asyncio

import pytest

from src.repository import Repository
from src.util import json as ujson
from src.util.map import Area, _is_inside


class Node:
    def __init__(self, name):
        self.domain = type("D", (), {"name": name})()


@pytest.mark.asyncio
async def test_repository_retrieve_concurrent_with_mutation():
    r = Repository()

    async def register(i):
        await asyncio.sleep(0)
        r.append(Node(f"n{i}"))

    await asyncio.gather(*(register(i) for i in range(20)))
    assert len(r.retrieve(Node)) == 20
    assert [n.domain.name for n in r.retrieve(Node, name="n7")] == ["n7"]


@pytest.mark.asyncio
async def test_core_helpers_inside_event_loop():
    area = Area(name="a", vertex_list=[[0, 0], [0, 1], [1, 1], [1, 0]])
    results = await asyncio.gather(*(asyncio.to_thread(_is_inside, [0.5, 0.5], [area]) for _ in range(5)))
    assert all(results)
    assert ujson.dumps(area) == '{"name": "a", "vertex_list": [[0, 0], [0, 1], [1, 1], [1, 0]]}'
