import asyncio
import json
from pathlib import Path
import os
from contextlib import asynccontextmanager


def _load_json(path: Path):
    with path.open() as f:
        return json.load(f)


async def load_json(path: Path):
    return await asyncio.to_thread(_load_json, path)


def _dump_json(obj, path: Path, *, fsync=False):
    with path.open('w') as f:
        json.dump(obj, f)
        if fsync:
            f.flush()
            os.fsync(f)


async def dump_json(obj, path: Path, *, fsync=False):
    await asyncio.to_thread(_dump_json, obj, path, fsync=fsync)


def _add_suffix(path: Path, suffix: str):
    return path.with_suffix(path.suffix + suffix)


def temp_replace(path: Path):
    """Creates a temporary file path on entry, which on exit will replace the given path if no exception occurs

    This function will not flush or sync for you."""
    temp_path = _add_suffix(path, ".temp")
    try:
        yield temp_path
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)


class RWLock:
    """A writer-preferring asyncio read-write lock."""
    def __init__(self):
        self._write_lock = asyncio.Lock()
        self._allow_write = asyncio.Event()
        self._allow_read = asyncio.Event()
        self._readers = 0

    @asynccontextmanager
    async def reading(self):
        await self._allow_read.wait()
        self._readers += 1
        self._allow_write.clear()
        try:
            yield
        finally:
            self._readers -= 1
            if self._readers == 0:
                self._allow_write.set()

    @asynccontextmanager
    async def writing(self):
        async with self._write_lock:
            self._allow_read.clear()
            await self._allow_write.wait()
            try:
                yield
            finally:
                self._allow_read.set()
