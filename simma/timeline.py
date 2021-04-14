import asyncio
from pathlib import Path
from uuid import UUID
from typing import Optional
import json
import re
import aiosqlite
from datetime import datetime
from contextlib import asynccontextmanager
from bisect import insort


_REGEX_POINT_NAME_EXP = re.compile(r'^tick-(?P<tick>\d+)\.point$')


class TimelineData:
    def __init__(self, path: Path):
        self.path: Path = path.resolve(False).absolute()
        self.ticks = []
        self._pending_ticks = set()

    def _get_point_file_path(self, tick):
        return self.path / f'tick-{tick}.point'

    def _get_db_path(self):
        return self.path / 'timeline.db'

    async def create(self):
        self.path.mkdir(exist_ok=False)
        async with self.get_db_conn() as db, _committing(db):
            await db.execute('''
                        CREATE TABLE IF NOT EXISTS events (
                            tick INTEGER NOT NULL,
                            event_name TEXT,
                            event_json TEXT,
                            PRIMARY KEY(tick, event_name)
                        )''')
            await db.execute('''
                        CREATE TABLE IF NOT EXISTS meta (
                            id INTEGER PRIMARY KEY CHECK (id = 0),
                            last_commit_timestamp TEXT
                        )''')
            await db.execute('''
                        INSERT OR IGNORE INTO
                        meta(id, last_commit_timestamp)
                        VALUES(0,?)
                        ''', (datetime.utcnow().isoformat(),))

    async def load(self):
        await asyncio.to_thread(self._load_ticks)

    def _load_ticks(self):
        ticks = []
        for tick, _ in self.get_points():
            ticks.append(tick)
        ticks.sort()
        self.ticks = ticks

    def get_db_conn(self):
        return aiosqlite.connect(self._get_db_path())

    def get_points(self):
        for point_path in self.path.glob('*.point'):
            tick = _parse_point_file(point_path.name)
            yield tick, point_path

    async def add_binary_point(self, tick, binary, overwrite=False):
        if (
            not overwrite
            and (
                tick in self._pending_ticks
                or tick in self.ticks
            )
        ):
            return

        self._pending_ticks.add(tick)
        point_file = self._get_point_file_path(tick)
        temp_file = point_file.with_suffix('.ptemp')
        try:
            def do_write():
                with temp_file.open('bw') as f:
                    f.write(binary)
            await asyncio.to_thread(do_write)
            temp_file.rename(point_file)
            if tick not in self.ticks:
                insort(self.ticks, tick)
        finally:
            self._pending_ticks.remove(tick)
            temp_file.unlink(missing_ok=True)


class ProjectTimeline:
    def __init__(self, path: Path):
        self.path = path

        self.data: TimelineData = TimelineData(path / 'data')

        self.uuid: Optional[UUID] = None
        self.parent_uuid: Optional[UUID] = None
        self.binary_uuid: Optional[UUID] = None
        self.tags = set()

    def _config_path(self):
        return self.path / 'timeline.json'

    async def create(self):
        self.path.mkdir(exist_ok=False)
        await self.data.create()
        self.save()

    async def load(self):
        with self._config_path().open('r') as f:
            config = json.load(f)

        uuid = config.get('uuid')
        if uuid:
            uuid = UUID(uuid)
        self.uuid = uuid

        parent_uuid = config.get('parent_uuid')
        if parent_uuid:
            parent_uuid = UUID(parent_uuid)
        self.parent_uuid = parent_uuid

        binary_uuid = config.get('binary_uuid')
        if binary_uuid:
            binary_uuid = UUID(binary_uuid)
        self.binary_uuid = binary_uuid

        tags = config.get('tags')
        if tags:
            self.tags = set(config['tags'])
        else:
            self.tags = set()

        await self.data.load()

    def save(self):
        config = {
            'uuid': str(self.uuid) if self.uuid else None,
            'parent_uuid': str(self.parent_uuid) if self.parent_uuid else None,
            'binary_uuid': str(self.binary_uuid) if self.binary_uuid else None,
            'tags': list(self.tags)
        }

        with self._config_path().open('w') as f:
            json.dump(config, f)


@asynccontextmanager
async def _committing(db_conn: aiosqlite.Connection):
    """Commits changes to a connection if no exceptions occur, otherwise rolls back"""
    try:
        yield
        await db_conn.commit()
    except: # noqa
        await db_conn.rollback()
        raise


def _parse_point_file(file_name):
    result = _REGEX_POINT_NAME_EXP.match(file_name)
    if result:
        return int(result.group('tick'))
    else:
        return None



