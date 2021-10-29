import asyncio
import json
from pathlib import Path
import os
from contextlib import asynccontextmanager, contextmanager
from inspect import ismethod
import weakref
from typing import Optional, Callable, TypeVar


T = TypeVar('T')


fsync = os.fsync


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


@contextmanager
def temp_replace(path: Path, temp_path: Path = None):
    """Creates a temporary file path on entry, which on exit will replace the given path if no exception occurs

    This function will not flush or sync for you."""
    if temp_path is None:
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
        self._allow_upgrade = asyncio.Event()
        self._allow_read = asyncio.Event()
        self._readers = 0
        self._upgrader_id = 0

    @asynccontextmanager
    async def reading(self):
        await self._allow_read.wait()
        self._readers += 1
        self._allow_write.clear()
        if self._readers > 1:
            self._allow_upgrade.clear()
        try:
            yield
        finally:
            self._readers -= 1
            if self._readers == 1:
                self._allow_upgrade.set()
            elif self._readers == 0:
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

    def _make_upgrader(self):
        self._upgrader_id += 1
        my_upgrader_id = self._upgrader_id

        @asynccontextmanager
        async def upgrader():
            if self._upgrader_id != my_upgrader_id:
                raise RuntimeError("Tried to upgrade with expired upgrader.")
            self._allow_read.clear()
            await self._allow_upgrade.wait()
            try:
                yield
            finally:
                self._allow_read.set()

        return upgrader

    @asynccontextmanager
    async def reading_upgradable(self):
        async with self._write_lock, self.reading():
            yield self._make_upgrader()


class Signal:
    """
    A signal is an observable object. Callables can be connected to the signal,
    which will then be called whenever the signal is emitted.
    The order that connected callbacks are called is undefined. It is only guaranteed that each connected
    callback will be called exactly once for each time the signal is emitted.
    """
    __slots__ = ('_callbacks',)

    def __init__(self):
        self._callbacks: list[tuple[Optional[weakref.ref], Callable, tuple]] = []

    def connect(self, callback, *binds):
        """
        Connects a callback to the signal. Whenever the signal is emitted, the callback will be called.
        :param callback: callable to connect to the signal
        :param binds: additional parameters that should be passed to the callback whenever the signal is emitted
        """
        if ismethod(callback):
            # Bound method case
            self_weakref = weakref.ref(callback.__self__)
            self._callbacks.append((self_weakref, callback.__func__, binds))
        else:
            # Function/callable case
            self._callbacks.append((None, callback, binds))

    def disconnect(self, callback):
        """
        Disconnect a given callback from the signal.
        The callback will no longer be called whenever the signal is emitted.
        :param callback: Callable to disconnect.
        """
        i = self._find_callback(callback)
        self._remove_index(i)

    def emit(self, *args):
        """
        Emits the signal, calling all connected callbacks with the provided args.
        :param args: Args to pass to each callback
        """
        for i in range(len(self._callbacks) - 1, -1, -1):
            ref, callback, binds = self._callbacks[i]

            if ref is not None:
                # Bound method case
                obj = ref()
                if obj is not None:
                    callback(obj, *args, *binds)
                else:
                    # slot object was deleted earlier, remove it.
                    self._remove_index(i)
            else:
                # Function case
                callback(*args, *binds)

    def _find_callback(self, callback):
        if ismethod(callback):
            # Bound method case
            expected_self = callback.__self__
            expected_callback = callback.__func__
        else:
            # Function/callable case
            expected_self = None
            expected_callback = callback

        for i, (ref, callback, binds) in enumerate(self._callbacks):
            found_self = None
            if ref is not None:
                found_self = ref()
                if found_self is None:
                    continue

            if found_self is expected_self and callback is expected_callback:
                return i

        raise ValueError("Unable to find a connection with the given slot.")

    def _remove_index(self, index):
        """
        Removes an item from the callback list by putting the last item into its position. This makes this an O(1)
        operation, at the expense of making callback calling order undefined.
        :param index: Index to remove from the slots list.
        """
        if index == len(self._callbacks) - 1 or index == -1:
            self._callbacks.pop()
        else:
            self._callbacks[index] = self._callbacks.pop()
