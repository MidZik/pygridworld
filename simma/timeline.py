import asyncio
from pathlib import Path
from typing import Callable
import re
import aiosqlite
from datetime import datetime
from contextlib import asynccontextmanager
import shutil
import warnings

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
    _CONFIG_FILE_NAME = 'timeline.json'
    _METADATA_FILE_NAME = 'metadata.json'

    @staticmethod
    async def open(path: Path, exist_ok=True):
        path.mkdir(exist_ok=exist_ok)

        timeline = Timeline(path)
        timeline._points_dir_path().mkdir(exist_ok=True)

        async with timeline.get_db_conn() as db, _committing(db):
            await db.execute('''
                        CREATE TABLE IF NOT EXISTS events (
                            tick INTEGER NOT NULL,
                            event_name TEXT,
                            event_json TEXT,
                            PRIMARY KEY(tick, event_name)
                        )''')

        # if a transaction was in progress, abort it or commit it as appropriate
        # (_abort_transact will not abort a transaction that is ready for commit)
        await timeline._abort_transact()
        await timeline._commit_transact()

        config_data = await _utils.load_json(timeline.path / Timeline._CONFIG_FILE_NAME)
        timeline.head_tick = int(config_data['head_tick'])

        timeline._ready = True
        return timeline

    @staticmethod
    def _get_point_file_name(tick):
        return f'tick-{tick}.point'

    def __init__(self, path: Path):
        self.path = path

        # A timeline will never have a negative head_tick. -1 is only used until a the proper
        # head tick is loaded.
        self.head_tick = -1

        self._ready = False
        self._in_progress_ticks = set()

    def _points_dir_path(self):
        return self.path / 'points'

    def _get_point_path(self, tick):
        return self.path / self._get_point_file_name(tick)

    def _transact_prep_dir_path(self):
        return self.path / '_transact_prep'

    def _transact_ready_dir_path(self):
        return self.path / '_transact_ready'

    def _transact_committing_dir_path(self):
        return self.path / '_transact_committing'

    def _get_db_path(self):
        return self.path / 'timeline.db'

    def _assert_ready(self):
        if not self._ready:
            raise RuntimeError("Timeline is not ready for operations.")

    async def _abort_transact(self):
        if self._transact_prep_dir_path().is_dir():
            await asyncio.to_thread(shutil.rmtree, self._transact_prep_dir_path())

    async def _commit_transact(self):
        # part 1 of commit: delete all existing if the timeline is in the ready phase
        points_dir = self._points_dir_path()
        ready_dir = self._transact_ready_dir_path()
        committing_dir = self._transact_committing_dir_path()
        if ready_dir.is_dir():
            # delete all existing data + ticks
            def delete_all_points():
                for point_path in points_dir.glob('*.point'):
                    point_path.unlink()

            async def delete_all_events():
                async with self.get_db_conn() as db, _committing(db):
                    await db.execute('DELETE FROM events')

            await asyncio.gather(asyncio.to_thread(delete_all_points), delete_all_events())

            ready_dir.rename(committing_dir)

        # part 2 of commit: move committed data where it belongs
        if committing_dir.is_dir():
            new_config = await _utils.load_json(self._transact_ready_dir_path() / Timeline._CONFIG_FILE_NAME)
            self.head_tick = int(new_config['head_tick'])
            new_head_tick_file_name = self._get_point_file_name(self.head_tick)

            files_to_move = [
                (Timeline._CONFIG_FILE_NAME, Timeline._CONFIG_FILE_NAME),
                (Timeline._METADATA_FILE_NAME, Timeline._METADATA_FILE_NAME),
                (new_head_tick_file_name, f"points/{new_head_tick_file_name}")
            ]

            for src, dst in files_to_move:
                src_path = committing_dir / src
                dst_path = self.path / dst

                if src_path.exists():
                    src_path.replace(dst_path)

            committing_dir.unlink()

    def get_db_conn(self):
        return aiosqlite.connect(self._get_db_path())

    def get_points(self):
        self._assert_ready()
        for point_path in self._points_dir_path().glob('*.point'):
            tick = _parse_point_file(point_path.name)
            if tick is None or tick < self.head_tick:
                warnings.warn(f"Invalid point '{point_path.name}' found in timeline {self.path}", RuntimeWarning)
                continue
            yield tick, point_path

    def get_point(self, tick):
        self._assert_ready()
        if tick < self.head_tick:
            raise ValueError("Cannot get point of tick earlier than the head tick.")

        point_path = self._get_point_path(tick)
        if point_path.exists():
            return point_path
        else:
            raise FileNotFoundError("No point exists for the specified tick.")

    def has_point(self, tick):
        self._assert_ready()
        if tick < self.head_tick:
            raise ValueError("Cannot get point of tick earlier than the head tick.")

        point_path = self._get_point_path(tick)
        return point_path.is_file()

    async def add_point(self, tick, point_creator: Callable[[Path], None]):
        """ Adds a new point to the timeline. Must come after the head point.

        :param tick: The tick of the point
        :param point_creator: A callback that is provided a path. If the point needs to be created,
            the callback will be called, and should create the file at the given path with the point data.
        :return:
        """
        if tick <= self.head_tick:
            raise ValueError("Cannot add a point at or before the head point.")

        new_point_path = self._get_point_path(tick)

        # Never overwrite. If an add is in progress, or the point exists, do nothing.
        if tick in self._in_progress_ticks or new_point_path.exists():
            return

        await asyncio.to_thread(point_creator, new_point_path)

    async def add_point_via_copy(self, tick, point_data_path: Path):
        def copy(dest_path: Path):
            shutil.copyfile(point_data_path, dest_path)

        await self.add_point(tick, copy)

    async def add_point_via_move(self, tick, point_data_path: Path):
        def move(dest_path: Path):
            point_data_path.rename(dest_path)

        await self.add_point(tick, move)

    async def delete_point(self, tick):
        point_path = self._get_point_path(tick)
        point_path.unlink(missing_ok=True)

    async def reset(self, head_tick: int, head_data_path: Path, metadata=None, *, transfer_mode='copy'):
        """ Deletes all data in the timeline and resets it to a new head point, with optionally
        new metadata to go along with it.

        :param head_tick: the new head tick the timeline should have
        :param head_data_path: the file that contains the head tick data
        :param metadata: Any json-serializable data structure.
        :param transfer_mode: How to move the provided file into the timeline. Either 'copy' or 'move'.
            If 'copy', the file will be copied into the timeline. Otherwise, the file will be moved
            into the timeline (deleting it from its original location).
        :return:
        """
        # phase 1, prepare the transaction
        prep_dir = self._transact_prep_dir_path()
        prep_dir.mkdir(exist_ok=False)

        try:
            write_coros = []

            new_config_data = {
                'head_tick': head_tick,
                'last_reset': datetime.utcnow().isoformat()
            }
            new_config_path = prep_dir / Timeline._CONFIG_FILE_NAME
            write_coros.append(_utils.dump_json(new_config_data, new_config_path))

            if metadata is not None:
                new_metadata_path = prep_dir / Timeline._METADATA_FILE_NAME
                write_coros.append(_utils.dump_json(metadata, new_metadata_path))

            new_head_tick_path = self._get_point_file_name(head_tick)
            if transfer_mode == 'copy':
                write_coros.append(asyncio.to_thread(shutil.copyfile, head_data_path, new_head_tick_path))
            elif transfer_mode == 'move':
                head_data_path.rename(new_head_tick_path)
            else:
                raise ValueError("transfer_mode must be one of 'copy' or 'move'")

            await asyncio.gather(*write_coros)

            # Renaming the prep dir to the ready dir commits the changes
            await asyncio.to_thread(prep_dir.rename, self._transact_ready_dir_path())
        except BaseException:
            await self._abort_transact()
            raise
        else:
            # Phase 2, apply changes to the timeline
            self._ready = False
            await self._commit_transact()
            self._ready = True
