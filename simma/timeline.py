import asyncio
from pathlib import Path
from typing import Callable, Optional, Coroutine
import re
import aiosqlite
from contextlib import asynccontextmanager
import shutil
from os import fsync
from inspect import iscoroutinefunction

from . import _utils


_REGEX_POINT_NAME_EXP = re.compile(r'^tick-(?P<tick>\d+)\.point$')


@asynccontextmanager
async def _committing(db_conn: aiosqlite.Connection):
    """Commits changes to a connection if no exceptions occur, otherwise rolls back"""
    try:
        yield
        await db_conn.commit()
    except BaseException:
        await db_conn.rollback()
        raise


def _parse_point_file(file_name):
    result = _REGEX_POINT_NAME_EXP.match(file_name)
    if result:
        return int(result.group('tick'))
    else:
        return None


class Timeline:
    __slots__ = ('path', '_in_progress_ticks')

    _POINTS_DIR_NAME = 'points'
    _CONFIG_FILE_NAME = 'timeline.json'
    _METADATA_FILE_NAME = 'metadata.json'

    @staticmethod
    async def create(path: Path,
                     config,
                     metadata):
        path.mkdir(exist_ok=False)

        points_dir = path / Timeline._POINTS_DIR_NAME
        points_dir.mkdir()

        metadata_path = path / Timeline._METADATA_FILE_NAME
        with _utils.temp_replace(metadata_path) as temp_meta_path:
            await _utils.dump_json(metadata, temp_meta_path, fsync=True)

        config_path = path / Timeline._CONFIG_FILE_NAME
        with _utils.temp_replace(config_path) as temp_config_path:
            await _utils.dump_json(config, temp_config_path, fsync=True)
        return Timeline.load(path)

    @staticmethod
    async def load(path: Path):
        timeline = Timeline(path)

        async with timeline.get_db_conn() as db, _committing(db):
            await db.execute('''
                        CREATE TABLE IF NOT EXISTS events (
                            tick INTEGER NOT NULL,
                            event_name TEXT,
                            event_json TEXT,
                            PRIMARY KEY(tick, event_name)
                        )''')

        return timeline

    @staticmethod
    def _get_point_file_name(tick):
        return f'tick-{tick}.point'

    def __init__(self, path: Path):
        config_path = path / Timeline._CONFIG_FILE_NAME
        if not config_path.is_file():
            raise RuntimeError("path is not a timeline dir")

        self.path = path

        self._in_progress_ticks = set()

    def _points_dir_path(self):
        return self.path / Timeline._POINTS_DIR_NAME

    def _get_point_path(self, tick):
        return self.path / self._get_point_file_name(tick)

    def _get_db_path(self):
        return self.path / 'timeline.db'

    def get_db_conn(self):
        return aiosqlite.connect(self._get_db_path())

    async def get_points(self):
        for point_path in self._points_dir_path().glob('*.point'):
            tick = _parse_point_file(point_path.name)
            yield tick, point_path

    async def get_point(self, tick):
        point_path = self._get_point_path(tick)
        if point_path.exists():
            return point_path
        else:
            raise FileNotFoundError("No point exists for the specified tick.")

    async def has_point(self, tick):
        point_path = self._get_point_path(tick)
        return point_path.is_file()

    async def add_point(self, tick, point_creator: Callable[[Path], Optional[Coroutine]]):
        """ Adds a new point to the timeline. Must come after the head point.

        :param tick: The tick of the point
        :param point_creator: A callback that is provided a path. If the point needs to be created,
            the callback will be called, and should create the file at the given path with the point data.
        :return:
        """
        new_point_path = self._get_point_path(tick)

        # Never overwrite. If an add is in progress, or the point exists, do nothing.
        if tick in self._in_progress_ticks or new_point_path.exists():
            return

        self._in_progress_ticks.add(tick)
        try:
            if iscoroutinefunction(point_creator):
                await point_creator(new_point_path)
            else:
                await asyncio.to_thread(point_creator, new_point_path)
        finally:
            self._in_progress_ticks.remove(tick)

    async def add_point_via_copy(self, tick, point_data_path: Path):
        def copy(dst_path: Path):
            shutil.copyfile(point_data_path, dst_path)

        await self.add_point(tick, copy)

    async def add_point_via_move(self, tick, point_data_path: Path):
        def move(dst_path: Path):
            point_data_path.rename(dst_path)

        await self.add_point(tick, move)

    async def add_point_data(self, tick, point_data: bytes):
        def write_bytes(dst_path: Path):
            with open(dst_path, 'wb') as f:
                f.write(point_data)
                f.flush()
                fsync(f)

        await self.add_point(tick, write_bytes)

    async def delete_point(self, tick):
        point_path = self._get_point_path(tick)
        point_path.unlink(missing_ok=True)

    async def get_metadata(self):
        return await _utils.load_json(self.path / Timeline._METADATA_FILE_NAME)

    async def set_metadata(self, metadata):
        with _utils.temp_replace(self.path / Timeline._METADATA_FILE_NAME) as temp_file:
            await _utils.dump_json(metadata, temp_file, fsync=True)

    async def get_config(self):
        return await _utils.load_json(self.path / Timeline._CONFIG_FILE_NAME)
