import asyncio
import json
from pathlib import Path


def _load_json(path: Path):
    with path.open() as f:
        return json.load(f)


async def load_json(path: Path):
    return await asyncio.to_thread(_load_json, path)


def _dump_json(obj, path: Path):
    with path.open('w') as f:
        json.dump(obj, f)


async def dump_json(obj, path: Path):
    await asyncio.to_thread(_dump_json, obj, path)
