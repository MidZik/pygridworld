import asyncio
import shutil
from pathlib import Path
from uuid import UUID, uuid4
from typing import Optional, Generic, TypeVar
from abc import abstractmethod
from secrets import token_urlsafe
from contextlib import asynccontextmanager
from dataclasses import dataclass

from .simulation import process
from .project import Project, BinaryInfo


RunningContextT = TypeVar('RunningContextT', bound='RunningContext')


class ProcessOwner(Generic[RunningContextT]):
    class _EditorTokenContext:
        def __init__(self, owner: 'ProcessOwner'):
            self._owner = owner

        def get_editor(self):
            return self._owner._current_editor

        async def set_editor(self, editor_token: Optional[str]):
            if editor_token == "":
                editor_token = None
            await self._owner.client.set_editor_token(editor_token if editor_token else "")
            self._owner._current_editor = editor_token

    def __init__(self):
        self.owner_token: Optional[str] = None
        self.process: Optional[process.Process] = None
        self.client: Optional[process.Client] = None

        self._current_editor: Optional[str] = None
        self._edit_token_lock = asyncio.Lock()
        self._process_lock = asyncio.Lock()
        self._process_user_count = 0
        self._users: set[UUID] = set()

    @abstractmethod
    async def _get_binary_path(self) -> Path:
        pass

    @abstractmethod
    async def _init_process(self, client: process.Client):
        pass

    @abstractmethod
    def _get_running_context(self, user_token: str) -> RunningContextT:
        pass

    @asynccontextmanager
    async def running(self):
        async with self._process_lock:
            self._process_user_count += 1
            if self.process is None:
                self.owner_token = token_urlsafe(32)
                binary_path = await self._get_binary_path()
                self.process = await process.start_simulation_process(binary_path, self.owner_token)
                self.client = self.process.make_client()
                await self._init_process(self.client)
        running_context = None
        new_user_token = token_urlsafe(32)
        try:
            self._users.add(new_user_token)
            running_context = self._get_running_context(new_user_token)
            yield running_context
        finally:
            self._users.remove(new_user_token)
            if running_context is not None:
                running_context.kill_context()
            async with self._process_lock:
                self._process_user_count -= 1
                if self._process_user_count == 0:
                    await self.process.stop()
                    self.owner_token = None
                    self.process = None
                    self.client = None

    @asynccontextmanager
    async def editor_token_context(self):
        async with self._edit_token_lock:
            editor_modifier = self._EditorTokenContext(self)
            yield editor_modifier
            editor_modifier._sim = None

    @asynccontextmanager
    async def temp_owner_takeover(self):
        async with self.editor_token_context() as etc:
            old_token = etc.get_editor()
            await etc.set_editor(self.owner_token)
            try:
                yield
            finally:
                await etc.set_editor(old_token)

    def get_process_address(self):
        if self.process is None:
            return None
        else:
            return self.process.get_address()


class TimelineSimulator(ProcessOwner['TimelineSimulatorRunningContext']):
    def __init__(self, project: Project, timeline_id: UUID):
        super().__init__()
        self.project = project
        self.timeline_id = timeline_id

    async def _get_binary_path(self):
        timeline_info = await self.project.get_timeline_info(self.timeline_id)
        binary_info = await self.project.get_binary_info(timeline_info.binary_id)
        return binary_info.binary_path

    async def _init_process(self, client: process.Client):
        points = await self.project.get_timeline_points(self.timeline_id)
        _, last_point_path = points[-1]
        state_binary = await asyncio.to_thread(last_point_path.read_bytes)
        async with self.temp_owner_takeover():
            await client.set_state_binary(state_binary)

    def _get_running_context(self, user_token: str):
        return TimelineSimulatorRunningContext(self, user_token)


class TimelineCreator(ProcessOwner['TimelineCreatorRunningContext']):
    def __init__(self, project: Project, binary_id: UUID, initial_timeline_id: UUID, tick: int):
        super().__init__()
        self.project = project
        self.binary_id = binary_id
        self.initial_timeline_id = initial_timeline_id
        self.tick = tick

        self.parent_id = None

        self.current_editor = None

    async def _get_binary_path(self) -> Path:
        binary_info = await self.project.get_binary_info(self.binary_id)
        return binary_info.binary_path

    async def _init_process(self, client: process.Client):
        timeline_info = await self.project.get_timeline_info(self.initial_timeline_id)
        if self.tick == timeline_info.head_tick:
            self.parent_id = timeline_info.parent_id
        else:
            self.parent_id = self.initial_timeline_id

        point_path = await self.project.get_timeline_point(self.initial_timeline_id, self.tick)
        state_binary = await asyncio.to_thread(point_path.read_bytes)
        async with self.editor_token_context() as etc:
            etc.set_editor(self.owner_token)
            await client.set_state_binary(state_binary)
            etc.set_editor(token_urlsafe(32))

    def _get_running_context(self, user_token: str):
        return TimelineCreatorRunningContext(self, user_token)


ProcessOwnerT = TypeVar('ProcessOwnerT', bound=ProcessOwner)


class RunningContext(Generic[ProcessOwnerT]):
    def __init__(self, owner: ProcessOwnerT, user_token: str):
        self.owner = owner
        self.user_token = user_token

    def kill_context(self):
        self.owner = None

    def get_process_address(self):
        return self.owner.get_process_address()


class TimelineSimulatorRunningContext(RunningContext[TimelineSimulator]):
    async def move_to_tick(self, tick: int):
        client = self.owner.client
        project = self.owner.project
        timeline_id = self.owner.timeline_id
        point_path = await project.get_timeline_point(timeline_id, tick)
        if point_path:
            binary = await asyncio.to_thread(point_path.read_bytes)
            await client.set_state_binary(binary)

    async def save_state_to_new_point(self):
        client = self.owner.client
        project = self.owner.project
        timeline_id = self.owner.timeline_id
        binary, tick = await client.get_state_binary()
        existing_tick = await project.get_timeline_point(timeline_id, tick)
        if existing_tick is None:
            temp_path = project.get_temp_path()
            await asyncio.to_thread(temp_path.write_bytes, binary)
            await project.add_timeline_point(temp_path, timeline_id, tick)
            return tick
        else:
            return None


class TimelineCreatorRunningContext(RunningContext[TimelineCreator]):
    @asynccontextmanager
    async def editor(self, editor_token: str):
        if not editor_token:
            raise ValueError("Must specify a non-empty editor token to edit.")
        async with self.owner.editor_token_context() as etc:
            if self.owner.current_editor:
                raise RuntimeError("Only one editor is allowed at a time.")
            await etc.set_editor(editor_token)
            self.owner.current_editor = editor_token
        try:
            yield TimelineCreatorEditorContext(self.owner)
        finally:
            async with self.owner.editor_token_context() as etc:
                # resetting the editor token to a random token ensures that
                # the simulation cannot run while no editor is assigned.
                etc.set_editor(token_urlsafe(32))
                self.owner.current_editor = None


class TimelineCreatorEditorContext:
    def __init__(self, timeline_creator: TimelineCreator):
        self._creator = timeline_creator

    async def load_state(self, timeline_id: UUID):
        project = self._creator.project
        client = self._creator.client
        parent_id = self._creator.parent_id
        tick = self._creator.tick
        timeline_info = await project.get_timeline_info(timeline_id)
        is_sibling = (timeline_info.parent_id == parent_id
                      and timeline_info.head_tick == tick)
        is_parent = (timeline_info.timeline_id == parent_id)
        if not is_sibling and not is_parent:
            raise ValueError("Can only load state from a sibling timeline or the parent timeline.")
        point_to_load = await project.get_timeline_point(timeline_id, tick)
        if point_to_load is None:
            raise RuntimeError(f"Could not load point for tick {tick} in timeline {timeline_id}")
        async with self._creator.temp_owner_takeover():
            state_binary = await asyncio.to_thread(point_to_load.read_bytes)
            await client.set_state_binary(state_binary)

    async def save_state_as_new_timeline(self):
        client = self._creator.client
        project = self._creator.project
        parent_id = self._creator.parent_id
        binary_id = self._creator.binary_id
        binary, tick = await client.get_state_binary()
        temp_path = project.get_temp_path()
        await asyncio.to_thread(temp_path.write_bytes, binary)
        return await project.create_timeline(temp_path, binary_id, parent_id, tick)


@dataclass
class ProcessContainer(Generic[ProcessOwnerT]):
    user_count: int
    process: ProcessOwnerT


class ProjectService:
    def __init__(self, project_path: Path):
        self._project = Project.load(project_path)
        self._timeline_simulators: dict[UUID, ProcessContainer[TimelineSimulator]] = {}
        self._timeline_creators: dict[UUID, ProcessContainer[TimelineCreator]] = {}

    @staticmethod
    def _validate_tags(tags):
        if not all(len(tag) <= 100 for tag in tags):
            raise ValueError("Tags cannot exceed 100 characters in length.")

    async def add_local_binary(self, simbin_path: Path):
        return await self._project.add_binary(simbin_path)

    async def get_binary(self, binary_id: UUID):
        return await self._project.get_binary_info(binary_id)

    async def get_binary_description(self, binary_id: UUID):
        return await self._project.get_binary_description(binary_id)

    async def set_binary_description(self, binary_id: UUID, description: str):
        return await self._project.set_binary_description(binary_id, description)

    async def set_binary_name(self, binary_id: UUID, name: str):
        return await self._project.set_binary_name(binary_id, name)

    async def delete_binary(self, binary_id: UUID):
        return await self._project.delete_binary(binary_id)

    async def _create_timeline_head_point(self,
                                          source_path: Path,
                                          source_binary: BinaryInfo,
                                          target_binary: BinaryInfo):
        temp_path = self._project.get_temp_path()
        try:
            if source_path is None:
                await process.create_default(str(temp_path), 'bin', str(target_binary.binary_path))
            else:
                if source_binary.binary_id == target_binary.binary_id:
                    await asyncio.to_thread(shutil.copy2, source_path, temp_path)
                else:
                    await process.simple_convert(str(source_path), 'bin', str(source_binary.binary_path),
                                                 str(temp_path), 'bin', str(target_binary.binary_path))
            return temp_path
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise

    async def create_default_timeline(self,
                                      binary_id: UUID,
                                      head_tick: Optional[int] = None,
                                      parent_timeline_id: Optional[UUID] = None
                                      ):
        if head_tick is not None and head_tick < 0:
            raise ValueError("Head tick must be a non-negative integer.")

        if parent_timeline_id is not None:
            parent_timeline_info = await self._project.get_timeline_info(parent_timeline_id)

            if binary_id == parent_timeline_info.binary_id:
                raise ValueError("Default timeline with parent must have a different binary than parent.")

            if head_tick is None:
                head_tick = parent_timeline_info.head_tick

            if head_tick == parent_timeline_info.head_tick:
                source_point = parent_timeline_info.head_path
            else:
                source_point = await self._project.get_timeline_point(parent_timeline_id, head_tick)
                if source_point is None:
                    raise ValueError("A head tick was specified that doesn't exist as a point of the parent.")
            source_binary_info = await self._project.get_binary_info(parent_timeline_info.binary_id)
        else:
            source_binary_info = None
            source_point = None

        binary_info = await self._project.get_binary_info(binary_id)

        temp_head_point = await self._create_timeline_head_point(source_point, source_binary_info, binary_info)

        await self._project.create_timeline(temp_head_point, binary_id, parent_timeline_id, head_tick)

    async def get_timeline(self, timeline_id: UUID):
        return await self._project.get_timeline_info(timeline_id)

    async def find_timelines(self, filter_parents=(), require_tags=(), disallow_tags=()):
        self._validate_tags(require_tags)
        self._validate_tags(disallow_tags)
        return await self._project.find_timeline_infos(filter_parents, require_tags, disallow_tags)

    async def delete_timeline(self, timeline_id: UUID):
        return await self._project.delete_timeline(timeline_id)

    async def modify_timeline_tags(self, *timeline_ids: UUID, tags_to_add=(), tags_to_remove=()):
        self._validate_tags(tags_to_add)
        self._validate_tags(tags_to_remove)
        return await self._project.modify_timeline_tags(*timeline_ids,
                                                        tags_to_add=tags_to_add,
                                                        tags_to_remove=tags_to_remove)

    async def get_timeline_point(self, timeline_id: UUID, tick: int):
        return await self._project.get_timeline_point(timeline_id, tick)

    async def get_timeline_points(self, timeline_id: UUID):
        return await self._project.get_timeline_points(timeline_id)

    async def get_timeline_tags(self, timeline_id: UUID):
        return await self._project.get_timeline_tags(timeline_id)

    @asynccontextmanager
    async def timeline_point_json_generator(self, timeline_id: UUID):
        """Returns a generator that accepts paths to binary point data of the given timeline,
        and yields JSON string representations of the binary data."""
        timeline = await self._project.get_timeline_info(timeline_id)
        binary = await self._project.get_binary_info(timeline.binary_id)

        converter_generator = process.convert_multiple_generator('binary', str(binary.binary_path), 'json')
        await converter_generator.asend(None)
        try:
            yield converter_generator
        finally:
            try:
                await converter_generator.asend(None)
            except StopAsyncIteration:
                pass

    async def get_timeline_events(self, timeline_id, *, start_tick=None, end_tick=None, event_name_filters=None):
        """
        :param timeline_id:
        :param start_tick:
        :param end_tick:
        :param event_name_filters: A collection of event name filters. Only event names matching the provided filters
            will be returned. Filter names which end in a period (.) will include all events that start with it,
            otherwise it will only return exact matches.
        :return: A generator of (tick, event_name, event_json) tuples, containing the requested event data.
        Events will be returned in ascending tick order, with no guarantee that events within a single tick
        will be consistently ordered.
        """
        query = "SELECT tick, event_name, event_json FROM events"
        where_clauses = []
        parameters = []

        if start_tick is not None:
            where_clauses.append("tick >= ?")
            parameters.append(start_tick)

        if end_tick is not None:
            where_clauses.append("tick <= ?")
            parameters.append(end_tick)

        if event_name_filters:
            filter_clauses = []
            filter_parameters = []
            for f in event_name_filters:
                if f.contains('\\'):
                    raise ValueError("Filters cannot contain backslashes (\\).")
                filter_clauses += r"event_name LIKE ? ESCAPE '\'"
                f = f.replace(r'%', r'\%').replace(r'_', r'\_')
                if f.endswith('.'):
                    filter_parameters.append(f + '%')
                else:
                    filter_parameters.append(f)

            where_clauses.append(" OR ".join(filter_clauses))
            parameters.extend(filter_parameters)

        if where_clauses:
            query += " WHERE ("
            query += ") AND (".join(where_clauses)
            query += ")"

        query += " ORDER BY tick ASC"

        async with self._project.timeline_event_db_connection(timeline_id) as db:
            async with db.execute(query, tuple(parameters)) as cursor:
                async for row in cursor:
                    yield tuple(row)

    async def delete_timeline_points(self, timeline_id: UUID, *ticks_to_delete: int):
        return await self._project.delete_timeline_points(timeline_id, *ticks_to_delete)

    @asynccontextmanager
    async def timeline_simulator(self, timeline_id: UUID):
        if timeline_id not in self._timeline_simulators:
            container = ProcessContainer(0, TimelineSimulator(self._project, timeline_id))
            self._timeline_simulators[timeline_id] = container
        else:
            container = self._timeline_simulators[timeline_id]
        container.user_count += 1
        sim: TimelineSimulator = container.process
        try:
            async with sim.running() as running_context:
                yield running_context
        finally:
            container.user_count -= 1
            if container.user_count == 0:
                del self._timeline_simulators[timeline_id]

    @asynccontextmanager
    async def new_timeline_creator(self, binary_id: UUID, initial_timeline_id: UUID, tick: int):
        creator_id = uuid4()
        container = ProcessContainer(0, TimelineCreator(self._project, binary_id, initial_timeline_id, tick))
        self._timeline_creators[creator_id] = container
        container.user_count += 1
        creator = container.process
        try:
            async with creator.running() as running_context:
                yield creator_id, running_context
        finally:
            pass

    @asynccontextmanager
    async def existing_timeline_creator(self, creator_id: UUID):
        container = self._timeline_creators[creator_id]
        container.user_count += 1
        creator = container.process
        try:
            async with creator.running() as running_context:
                yield running_context
        finally:
            container.user_count -= 1
            if container.user_count == 0:
                del self._timeline_creators[creator_id]
