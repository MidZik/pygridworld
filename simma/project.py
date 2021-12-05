import aiosqlite
import appdirs
import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil
from typing import Optional
from uuid import uuid4, UUID

from .binary import LocalSimbin, PackedSimbin


def _user_data_path():
    return Path(appdirs.user_data_dir('simma', False))


@dataclass
class BinaryInfo:
    binary_id: UUID
    name: str
    creation_time: datetime
    description_head: str

    packed_simbin_dir: Path

    async def get_packed_simbin(self):
        return PackedSimbin.load_dir(self.packed_simbin_dir)


@dataclass
class TimelineInfo:
    timeline_id: UUID
    binary_id: UUID
    parent_id: Optional[UUID]
    head_tick: int
    creation_time: datetime

    head_path: Path


class Project:
    def __init__(self, path: Path):
        self._path = path.resolve()

    def _timeline_data_path(self, timeline_id: Optional[UUID] = None):
        path = self._path / 'timeline_data'
        if timeline_id:
            return path / str(timeline_id)
        else:
            return path

    @staticmethod
    def _path_timestamp(dt: datetime):
        return dt.strftime('%Y%m%d%H%M%S%f')

    def _timeline_point_path(self, timeline_id: UUID, tick: int, creation_time: datetime):
        return self._timeline_data_path(timeline_id) / f'tick{tick}-{self._path_timestamp(creation_time)}.point'

    def _timeline_head_path(self, timeline_id: UUID, head_tick: int, creation_time: datetime):
        return self._timeline_data_path(timeline_id) / f'head{head_tick}-{self._path_timestamp(creation_time)}.point'

    def _timeline_events_db_path(self, timeline_id: UUID):
        return self._timeline_data_path(timeline_id) / 'events.db'

    async def _init_timeline_events_db(self, timeline_id: UUID):
        db_path = self._timeline_events_db_path(timeline_id)
        async with aiosqlite.connect(db_path) as db:
            await db.execute('''
                CREATE TABLE event (
                    tick INTEGER NOT NULL,
                    name TEXT,
                    json TEXT,
                    PRIMARY KEY(tick, name)
                )''')
            await db.commit()

    def _binary_data_path(self, binary_id: Optional[UUID] = None):
        path = self._path / 'binary_data'
        if binary_id:
            return path / str(binary_id)
        else:
            return path

    def _temp_data_path(self):
        return self._path / 'temp'

    def _db_path(self):
        return self._path / 'project.db'

    def _db_connect(self):
        return aiosqlite.connect(self._db_path())

    @staticmethod
    def load(path: Path):
        project = Project(path.resolve(True))
        if (
                not project._db_path().is_file()
                or not project._timeline_data_path().is_dir()
                or not project._binary_data_path().is_dir()
        ):
            raise RuntimeError(f"Cannot load project at path {path}")
        else:
            return project

    @staticmethod
    async def create(path: Path):
        path = path.resolve()
        path.mkdir(exist_ok=True)
        if path.is_dir():
            if next(path.iterdir(), None) is not None:
                raise FileExistsError("Cannot create project in non-empty directory.")
        project = Project(path)

        project._timeline_data_path().mkdir()
        project._binary_data_path().mkdir()

        async with project._db_connect() as db:
            await db.execute('''
                CREATE TABLE binary (
                    id TEXT NOT NULL,
                    name TEXT,
                    filename TEXT NOT NULL,
                    creation_timestamp TEXT NOT NULL,
                    description TEXT,
                    PRIMARY KEY(id)
                )''')

            await db.execute('''
                CREATE TABLE timeline (
                    id TEXT NOT NULL,
                    binary_id TEXT NOT NULL,
                    parent_id TEXT,
                    head_tick INTEGER NOT NULL,
                    creation_timestamp TEXT NOT NULL,
                    PRIMARY KEY(id),
                    FOREIGN KEY(binary_id) REFERENCES binary(id),
                    FOREIGN KEY(parent_id) REFERENCES timeline(id)
                )''')

            await db.execute('''
                CREATE TABLE timeline_tag (
                    timeline_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY(timeline_id, tag),
                    FOREIGN KEY(timeline_id) REFERENCES timeline(id) ON DELETE CASCADE
                )''')

            await db.execute('''
                CREATE TABLE point (
                    timeline_id TEXT NOT NULL,
                    tick INTEGER NOT NULL,
                    creation_timestamp TEXT NOT NULL,
                    PRIMARY KEY(timeline_id, tick),
                    FOREIGN KEY(timeline_id) REFERENCES timeline(id)
                )''')

            await db.commit()

        return project

    def get_temp_path(self):
        return self._temp_data_path() / str(uuid4())

    def validate_temp_path(self, temp_path: Path, validate_exists=True):
        if temp_path.parent != self._temp_data_path():
            raise ValueError("temp_path is not inside project temp dir.")
        if validate_exists and not temp_path.is_file():
            raise FileNotFoundError('temp_path file does not exist.')

    async def add_binary(self, simbin_path: Path):
        local_simbin = await LocalSimbin.load(simbin_path)

        binary_id = uuid4()
        packed_simbin_path = self._binary_data_path(binary_id)

        try:
            packed_simbin = await PackedSimbin.create_from_local_simbin(packed_simbin_path, local_simbin)
            creation_time = datetime.utcnow()
            async with self._db_connect() as db:
                await db.execute('INSERT INTO binary VALUES (?,?,?,?,?)',
                                 (str(binary_id),
                                  packed_simbin.name,
                                  packed_simbin.binary_name,
                                  str(creation_time),
                                  ""))
                await db.commit()
            return BinaryInfo(binary_id, packed_simbin.name, creation_time, "", packed_simbin)
        except BaseException:
            await asyncio.to_thread(shutil.rmtree, packed_simbin_path)
            raise

    async def add_binary_from_packed_simbin(self, external_packed_simbin: PackedSimbin, move=False):
        binary_id = uuid4()
        packed_simbin_path = self._binary_data_path(binary_id)
        try:
            if move is True and external_packed_simbin.path.drive == packed_simbin_path.drive:
                external_packed_simbin.path.rename(packed_simbin_path)
            else:
                await asyncio.to_thread(shutil.copytree, external_packed_simbin.path, packed_simbin_path)
            packed_simbin = await PackedSimbin.load_dir(packed_simbin_path)
            creation_time = datetime.utcnow()
            async with self._db_connect() as db:
                await db.execute('INSERT INTO binary VALUES (?,?,?,?,?)',
                                 (str(binary_id),
                                  packed_simbin.name,
                                  packed_simbin.binary_name,
                                  str(creation_time),
                                  ""))
                await db.commit()
            return BinaryInfo(binary_id, packed_simbin.name, creation_time, "", packed_simbin)
        except BaseException:
            await asyncio.to_thread(shutil.rmtree, packed_simbin_path)
            raise

    async def get_binary_info(self, binary_id: UUID):
        """Returns a BinaryInfo object if the given binary exists. Otherwise returns None."""
        async with self._db_connect() as db:
            cursor: aiosqlite.Cursor = await db.execute(
                'SELECT name, filename, creation_timestamp, substr(description, 0, 100) FROM binary WHERE id = ?',
                (str(binary_id),)
            )
            result = await cursor.fetchone()
            if result is None:
                return None
            else:
                name, filename, creation_timestamp, description_head = result
                creation_time = datetime.fromisoformat(creation_timestamp)
                return BinaryInfo(binary_id, name, creation_time, description_head, self._binary_data_path(binary_id))

    async def get_all_binary_infos(self):
        """Yields a BinaryInfo object for every binary in the database."""
        async with self._db_connect() as db:
            cursor: aiosqlite.Cursor = await db.execute(
                'SELECT id, name, filename, creation_timestamp, substr(description, 0, 100) FROM binary'
            )
            while (result := await cursor.fetchone()) is not None:
                binary_id, name, filename, creation_timestamp, description_head = result
                binary_id = UUID(binary_id)
                creation_time = datetime.fromisoformat(creation_timestamp)
                yield BinaryInfo(binary_id, name, creation_time, description_head, self._binary_data_path(binary_id))

    async def get_binary_description(self, binary_id: UUID):
        async with self._db_connect() as db:
            cursor: aiosqlite.Cursor = await db.execute(
                'SELECT description FROM binary WHERE id = ?',
                (str(binary_id),)
            )
            description = await cursor.fetchone()
            return description

    async def set_binary_description(self, binary_id: UUID, description: str):
        if len(description) > 20000:
            raise RuntimeError("Description exceeds max length of 20000 characters.")
        async with self._db_connect() as db:
            await db.execute(
                'UPDATE binary SET description = ? WHERE id = ?',
                (description, str(binary_id))
            )
            await db.commit()

    async def set_binary_name(self, binary_id: UUID, name: str):
        if len(name) > 100:
            raise RuntimeError("Name exceeds max length of 100 characters.")
        async with self._db_connect() as db:
            await db.execute(
                'UPDATE binary SET name = ? WHERE id = ?',
                (name, str(binary_id))
            )

    async def delete_binary(self, binary_id: UUID):
        async with self._db_connect() as db:
            await db.execute(
                'DELETE FROM binary WHERE id = ?',
                (str(binary_id),)
            )
            await db.commit()

    async def create_timeline(self,
                              temp_head_path: Path,
                              binary_id: UUID,
                              parent_timeline_id: Optional[UUID] = None,
                              head_tick: int = 0):
        """Creates a timeline by consuming the file given at `temp_head_path` (by renaming the file).

        The temp_head_path file should be a value returned from `get_temp_path()`."""
        timeline_id = uuid4()
        creation_time = datetime.utcnow()
        head_point_destination = self._timeline_head_path(timeline_id, head_tick, creation_time)
        timeline_point_dir = head_point_destination.parent
        try:
            self.validate_temp_path(temp_head_path)
            async with self._db_connect() as db:
                await db.execute(
                    'INSERT INTO timeline VALUES (?,?,?,?,?)', (
                        str(timeline_id),
                        str(binary_id),
                        str(parent_timeline_id) if parent_timeline_id else None,
                        head_tick,
                        str(creation_time)
                    )
                )
                timeline_point_dir.mkdir(exist_ok=False)
                temp_head_path.rename(head_point_destination)
                await self._init_timeline_events_db(timeline_id)
                await db.commit()
            return TimelineInfo(timeline_id, binary_id, parent_timeline_id, head_tick, creation_time,
                                head_point_destination)
        except BaseException:
            head_point_destination.unlink(missing_ok=True)
            timeline_point_dir.rmdir()
            raise
        finally:
            temp_head_path.unlink(missing_ok=True)

    async def get_timeline_info(self, timeline_id: UUID):
        async with self._db_connect() as db:
            cursor: aiosqlite.Cursor = await db.execute(
                'SELECT id, binary_id, parent_id, head_tick, creation_timestamp FROM timeline WHERE id = ?',
                (str(timeline_id),)
            )
            timeline_id, binary_id, parent_id, head_tick, creation_timestamp = await cursor.fetchone()
            creation_time = datetime.fromisoformat(creation_timestamp)
            return TimelineInfo(timeline_id, binary_id, parent_id, head_tick, creation_time,
                                self._timeline_head_path(timeline_id, head_tick, creation_time))

    async def find_timeline_infos(self, filter_parents=(), require_tags=(), disallow_tags=()):
        filter_parents = set(filter_parents)
        require_tags = set(require_tags)
        disallow_tags = set(disallow_tags)
        require_tags.difference_update(disallow_tags)

        if len(filter_parents) > 1000:
            raise ValueError("Cannot filter over more than 1000 parents when searching for timelines.")
        if len(require_tags) > 50:
            raise ValueError("Cannot require over 50 tags when searching for timelines.")
        if len(disallow_tags) > 50:
            raise ValueError("Cannot disallow over 50 tags when searching for timelines.")

        async with self._db_connect() as db:
            await db.execute("CREATE TABLE temp.require_tag (tag TEXT NOT NULL)")
            await db.execute("CREATE TABLE temp.disallow_tag (tag TEXT NOT NULL)")
            await db.execute("CREATE TABLE temp.filter_parent (parent_id TEXT)")

            await db.executemany("INSERT INTO temp.require_tag(tag) VALUES (?)", zip(require_tags))
            await db.executemany("INSERT INTO temp.disallow_tag(tag) VALUES (?)", zip(disallow_tags))
            await db.executemany("INSERT INTO temp.filter_parent(parent_id) VALUES (?)", zip(filter_parents))

            cursor: aiosqlite.Cursor = await db.execute("""
                SELECT id, binary_id, parent_id, head_tick, creation_timestamp
                FROM timeline
                LEFT JOIN timeline_tag ON timeline.id = timeline_tag.timeline_id
                WHERE (
                    NOT EXISTS (SELECT * FROM temp.filter_parent) -- ignore this clause if there are no filtered parents
                    OR timeline.parent_id IN temp.filter_parent
                    OR (
                        EXISTS (SELECT * FROM temp.filter_parent WHERE temp.filter_parent.parent_id IS NULL)
                        AND timeline.parent_id IS NULL
                    )
                )
                AND (
                    NOT EXISTS (SELECT * FROM temp.require_tag) -- ignore this clause if there are no required tags
                    OR tag IN temp.require_tag
                )
                AND (
                    NOT EXISTS (SELECT * FROM temp.disallow_tag) -- ignore this clause if there are no disallowed tags
                    OR id NOT IN (
                        SELECT id
                        FROM timeline
                        LEFT JOIN timeline_tag ON timeline.id = timeline_tag.timeline_id
                        WHERE tag IN temp.disallow_tag
                    )
                )
                GROUP BY id
                HAVING (
                    NOT EXISTS (SELECT * FROM temp.require_tag) -- ignore this clause if there are no required tags
                    OR COUNT(id) = (SELECT COUNT(*) FROM temp.require_tag)
                )
                """)
            result = []
            row = await cursor.fetchone()
            while row:
                timeline_id, binary_id, parent_id, head_tick, creation_timestamp = row
                creation_time = datetime.fromisoformat(creation_timestamp)
                result.append(TimelineInfo(timeline_id, binary_id, parent_id, head_tick, creation_time,
                                           self._timeline_head_path(timeline_id, head_tick, creation_time)))
        return result

    async def delete_timeline(self, timeline_id: UUID):
        async with self._db_connect() as db:
            cursor: aiosqlite.Cursor = await db.execute(
                'SELECT head_tick, creation_timestamp FROM timeline WHERE id = ?',
                (str(timeline_id),)
            )
            result = await cursor.fetchone()
            if result is None:
                raise ValueError(f"Unable to find timeline with id {timeline_id}.")
            await db.execute(
                'DELETE FROM point WHERE timeline_id = ?',
                (str(timeline_id))
            )
            await db.execute(
                'DELETE FROM timeline WHERE id = ?',
                (str(timeline_id),)
            )
            await db.commit()
        timeline_dir_path = self._timeline_data_path(timeline_id)
        await asyncio.to_thread(shutil.rmtree, timeline_dir_path, ignore_errors=True)

    async def modify_timeline_tags(self, *timeline_ids: UUID, tags_to_add=(), tags_to_remove=()):
        timeline_ids = set(timeline_ids)
        tags_to_add = set(tags_to_add)
        tags_to_remove = set(tags_to_remove)
        tags_to_add.difference_update(tags_to_remove)

        if len(timeline_ids) > 1000:
            raise ValueError("Cannot modify tags for more than 1000 timelines at a time.")
        if len(tags_to_add) > 1000:
            raise ValueError("Cannot add more than 1000 tags at a time.")
        if len(tags_to_remove) > 1000:
            raise ValueError("Cannot remove more than 1000 tags at a time.")

        async with self._db_connect() as db:
            await db.execute("CREATE TABLE temp.modifying_id (timeline_id TEXT NOT NULL)")
            await db.execute("CREATE TABLE temp.add_tag (tag TEXT NOT NULL)")
            await db.execute("CREATE TABLE temp.remove_tag (tag TEXT NOT NULL)")

            await db.executemany("INSERT INTO temp.modifying_id(timeline_id) VALUES(?)", zip(timeline_ids))
            await db.executemany("INSERT INTO temp.add_tag(tag) VALUES (?)", zip(tags_to_add))
            await db.executemany("INSERT INTO temp.remove_tag(tag) VALUES (?)", zip(tags_to_remove))

            await db.execute("""
                DELETE FROM timeline_tag
                WHERE (timeline_id, tag) IN (
                    SELECT timeline_id, tag)
                    FROM temp.modifying_id
                    JOIN temp.remove_tag
                )""")
            await db.execute("""
                INSERT INTO timeline_tag
                SELECT timeline_id, tag
                FROM temp.modifying_id
                JOIN temp.add_tag
                """)

            await db.commit()

    async def add_timeline_point(self, temp_point_path: Path, timeline_id: UUID, tick: int):
        creation_time = datetime.utcnow()
        point_destination = self._timeline_point_path(timeline_id, tick, creation_time)
        try:
            self.validate_temp_path(temp_point_path)
            async with self._db_connect() as db:
                await db.execute(
                    'INSERT INTO points VALUES (?,?,?)', (
                        str(timeline_id),
                        tick,
                        str(creation_time)
                    )
                )
                temp_point_path.rename(point_destination)
                await db.commit()
        except BaseException:
            point_destination.unlink(missing_ok=True)
            raise
        finally:
            temp_point_path.unlink(missing_ok=True)

    async def get_timeline_point(self, timeline_id: UUID, tick: int):
        async with self._db_connect() as db:
            cursor: aiosqlite.Cursor = await db.execute(
                'SELECT creation_timestamp FROM point WHERE id = ? and tick = ?',
                (timeline_id, tick)
            )
            result = await cursor.fetchone()
        if result is not None:
            creation_time = datetime.fromisoformat(result[0])
            return self._timeline_point_path(timeline_id, tick, creation_time)
        else:
            return None

    async def get_timeline_points(self, timeline_id: UUID):
        async with self._db_connect() as db:
            cursor: aiosqlite.Cursor = await db.execute(
                'SELECT tick, creation_timestamp FROM point WHERE id = ? ORDER BY tick ASC',
                (timeline_id,)
            )
            results = await cursor.fetchall()
        return [(int(tick), self._timeline_point_path(timeline_id, tick, datetime.fromisoformat(creation_timestamp)))
                for tick, creation_timestamp in results]

    async def get_timeline_tags(self, timeline_id: UUID):
        async with self._db_connect() as db:
            cursor: aiosqlite.Cursor = await db.execute(
                'SELECT tag FROM tag WHERE timeline_id = ? ORDER BY tag ASC',
                (timeline_id,)
            )
            results = await cursor.fetchall()
            return [tag for (tag,) in results]

    async def delete_timeline_points(self, timeline_id: UUID, *ticks_to_delete: int):
        async with self._db_connect() as db:
            await db.execute(
                'CREATE TABLE temp.ticks_with_children (tick INTEGER UNIQUE);'
            )
            await db.execute(
                'CREATE TABLE temp.delete_ticks (tick INTEGER UNIQUE);'
            )
            await db.execute("""
                INSERT INTO temp.ticks_with_children(tick)
                SELECT head_tick FROM timeline WHERE parent_id = ?""",
                             (timeline_id,))
            await db.executemany("INSERT INTO temp.delete_ticks(tick) VALUES (?)", zip(ticks_to_delete))
            cursor: aiosqlite.Cursor = await db.execute(
                'SELECT tick, creation_timestamp FROM point '
                'WHERE id = ? and tick in temp.delete_ticks and tick not in temp.ticks_with_children',
                (timeline_id,)
            )
            deleted_tick_info = [(tick, creation_timestamp) for tick, creation_timestamp in await cursor.fetchall()]
            await db.execute(
                'DELETE FROM point '
                'WHERE id = ? and tick in temp.delete_ticks and tick not in temp.ticks_with_children',
                (timeline_id,)
            )
            await db.commit()
        for tick, creation_timestamp in deleted_tick_info:
            creation_time = datetime.fromisoformat(creation_timestamp)
            point = self._timeline_point_path(timeline_id, tick, creation_time)
            await asyncio.to_thread(point.unlink, missing_ok=True)

    async def timeline_event_db_connection(self, timeline_id: UUID):
        timeline_info = await self.get_timeline_info(timeline_id)
        if timeline_info is None:
            raise ValueError(f"Timeline {timeline_id} does not exist.")
        return aiosqlite.connect(self._timeline_events_db_path(timeline_id))
