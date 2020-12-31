"""
@author: Matt Idzik (MidZik)
"""
from collections import defaultdict, deque
from pathlib import Path
import json
import re
from typing import Optional, List
from bisect import insort
from simrunner import SimulationProcess
from dataclasses import dataclass
import sys
from datetime import datetime
from uuid import uuid4, UUID
import shutil
import subprocess
import os
import sqlite3


class Timeline:
    """
    Represents a timeline stored on disk
    """

    @staticmethod
    def point_file_name(tick):
        return f'tick-{tick}.point'

    @staticmethod
    def parse_point_file_name(file_name):
        exp = re.compile(r'^tick-(?P<tick>\d+)\.point$')
        result = exp.match(file_name)
        if result:
            return int(result.group('tick'))
        else:
            return None

    def __init__(self, path: Path, simulation_binary_provider):
        """
        :param path: The folder the timeline data resides in.
        """
        self.path: Path = path.resolve(True)
        self.simulation_binary_provider = simulation_binary_provider

        self.tick_list: List[int] = []

        self.refresh_tick_list()

        db_conn = self.get_db_conn()

        db_conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                tick INTEGER NOT NULL,
                event_name TEXT,
                event_json TEXT,
                PRIMARY KEY(tick, event_name)
            )''')
        db_conn.commit()

    def get_point_file_path(self, tick):
        return self.path / Timeline.point_file_name(tick)

    def get_db_path(self):
        return self.path / 'timeline.db'

    def get_db_conn(self):
        return sqlite3.connect(self.get_db_path())

    def head(self):
        return self.tick_list[0]

    def tail(self):
        return self.tick_list[-1]

    def get_simulation_binary_path(self):
        return self.simulation_binary_provider.get_simulation_binary_path()

    def refresh_tick_list(self):
        self.tick_list = []

        for point_path in self.path.glob('*.point'):
            tick = Timeline.parse_point_file_name(point_path.name)
            if tick is not None:
                self.tick_list.append(tick)

        self.tick_list.sort()


class TimelineSimulation:
    """
    Manages a SimulationRunnerProcess associated with a timeline.
    """

    def __init__(self, timeline):
        self.timeline: Timeline = timeline

        self._simulation_process: Optional[SimulationProcess] = None

        self._is_editing = False

    def is_editing(self):
        return self._is_editing

    def can_start_editing(self):
        # Can only edit the simulation state if:
        # 1. The simulation tick matches the head point tick.
        # 2. The head point is the only point in the timeline.
        # 3. Simulation is not currently running.
        # 4. Not currently in edit mode.
        timeline = self.timeline
        client = self._simulation_process.get_client()
        return (timeline.head() == timeline.tail() and
                client.get_tick() == timeline.head() and
                not client.is_running() and
                not self._is_editing)

    def start_editing(self):
        if self._is_editing:
            raise RuntimeError("Cannot start editing: already in edit mode.")

        if not self.can_start_editing():
            raise RuntimeError("Cannot start editing: not in an editable state.")

        self._is_editing = True

    def commit_edits(self):
        """
        Save the current simulation state as the new head point and exit edit mode.
        """
        if not self._is_editing:
            raise RuntimeError("Cannot commit edits: not in edit mode.")

        sim_state_binary = self.get_state_binary()
        head_point_path = self.timeline.get_point_file_path(self.timeline.head())
        with head_point_path.open('bw') as f:
            f.write(sim_state_binary)

        self._is_editing = False

    def discard_edits(self):
        """
        Revert the simulation state to the head point and exit edit mode.
        """
        if not self._is_editing:
            raise RuntimeError("Cannot discard edits: not in edit mode.")

        head_point_path = self.timeline.get_point_file_path(self.timeline.head())
        with head_point_path.open('br') as f:
            self.set_state_binary(f.read())

        self._is_editing = False

    def move_to_tick(self, tick: int):
        if tick not in self.timeline.tick_list:
            raise ValueError('Point tick is not part of simulation timeline.')

        if self._is_editing:
            raise RuntimeError('Cannot move to point while simulation is being edited.')

        if self.is_running():
            raise RuntimeError('Cannot move to point while simulation is running.')

        with self.timeline.get_point_file_path(tick).open('br') as f:
            self._simulation_process.get_client().set_state_binary(f.read())

    def start_process(self, initial_tick=None):
        if initial_tick is None:
            initial_tick = self.timeline.head()
        elif initial_tick not in self.timeline.tick_list:
            raise ValueError('Attempted to start timeline simulation at an invalid tick.')

        self._simulation_process = SimulationProcess(
            self.timeline.get_simulation_binary_path(),
            self._handle_event)
        self._simulation_process.start()

        self.move_to_tick(initial_tick)

    def stop_process(self):
        self._simulation_process.stop()

    def start_simulation(self):
        if not self._is_editing:
            self._simulation_process.get_client().start_simulation()

    def stop_simulation(self):
        self._simulation_process.get_client().stop_simulation()

    def is_running(self):
        return self._simulation_process.get_client().is_running()

    def get_tick(self):
        return self._simulation_process.get_client().get_tick()

    def get_state_json(self):
        return self._simulation_process.get_client().get_state_json()

    def set_state_json(self, state_json):
        if self._is_editing:
            self._simulation_process.get_client().set_state_json(state_json)

    def create_entity(self):
        if self._is_editing:
            return self._simulation_process.get_client().create_entity()

    def destroy_entity(self, eid):
        if self._is_editing:
            self._simulation_process.get_client().destroy_entity(eid)

    def get_all_entities(self):
        return self._simulation_process.get_client().get_all_entities()

    def assign_component(self, eid, com_name):
        if self._is_editing:
            self._simulation_process.get_client().assign_component(eid, com_name)

    def get_component_json(self, eid, com_name):
        return self._simulation_process.get_client().get_component_json(eid, com_name)

    def remove_component(self, eid, com_name):
        if self._is_editing:
            self._simulation_process.get_client().remove_component(eid, com_name)

    def replace_component(self, eid, com_name, state_json):
        if self._is_editing:
            self._simulation_process.get_client().replace_component(eid, com_name, state_json)

    def get_component_names(self):
        return self._simulation_process.get_client().get_component_names()

    def get_entity_component_names(self, eid):
        return self._simulation_process.get_client().get_entity_component_names(eid)

    def get_singleton_json(self, singleton_name):
        return self._simulation_process.get_client().get_singleton_json(singleton_name)

    def set_singleton_json(self, singleton_name, singleton_json):
        if self._is_editing:
            self._simulation_process.get_client().set_singleton_json(singleton_name, singleton_json)

    def get_singleton_names(self):
        return self._simulation_process.get_client().get_singleton_names()

    def get_new_client(self):
        return self._simulation_process.make_new_client()

    def get_state_binary(self):
        return self._simulation_process.get_client().get_state_binary()

    def set_state_binary(self, state_binary):
        if self._is_editing:
            self._simulation_process.get_client().set_state_binary(state_binary)

    def run_command(self, args):
        if args[0] == "sim" and not self._is_editing:
            return "'sim' command only allowed while in edit mode.", None
        return self._simulation_process.get_client().run_command(args)

    def _handle_event(self, tick, events):
        db_conn = self.timeline.get_db_conn()

        # Since many events can occur quite rapidly, enforcing sync with the disk can result
        # in excessive disk activity, and might cause writes to disk becoming a bottleneck.
        # Thus, we disable requiring a disk sync on every commit with this pragma.
        # This CAN cause the database to become corrupted in the event of a power loss,
        # but since the database can be easily reconstructed just by running the simulation,
        # this is not an important factor when compared to speed of handling events.
        db_conn.execute('PRAGMA synchronous = OFF')

        for e in events:
            if e.in_namespace("sim."):
                db_conn.execute('''
                INSERT OR IGNORE INTO
                events(tick, event_name, event_json)
                VALUES(?,?,?)
                ''', (tick, e.name, e.json))
            elif e.name == "meta.state_bin":
                if tick in self.timeline.tick_list:
                    continue
                else:
                    state_file_path = self.timeline.get_point_file_path(tick)
                    with state_file_path.open('bw') as state_file:
                        state_file.write(e.bin)
                    insort(self.timeline.tick_list, tick)

        db_conn.commit()


class TimelineNode:
    @staticmethod
    def traverse(root_node: 'TimelineNode', callback):
        """
        Traverses a node tree, calling the callback for each node in the tree.
        If callback returns a non-None value, traversal will stop immediately and its return value
        will be returned as the result of the traversal call
        :param root_node:
        :param callback:
        :return: If callback returns a non-None value for any node, it returns that value.
        Otherwise, it returns None after visiting every node.
        """
        traversal_deque = deque([root_node])
        while traversal_deque:
            cur_node = traversal_deque.pop()
            result = callback(cur_node)
            if result is not None:
                return result
            for child in cur_node.child_nodes:
                traversal_deque.append(child)

    def __init__(self,
                 parent_node: Optional['TimelineNode'] = None,
                 timeline_id: Optional[int] = None,
                 timeline: Optional[Timeline] = None):
        self.parent_node = parent_node
        self.timeline_id = timeline_id
        self.timeline = timeline
        self.child_nodes = []

        if parent_node is not None:
            parent_node.insert_child(self)

    def insert_child(self, child: 'TimelineNode'):
        insort(self.child_nodes, child)

    def previous_sibling(self):
        try:
            my_index = self.parent_node.child_nodes.index(self, 1)
            return self.parent_node.child_nodes[my_index - 1]
        except ValueError:
            return None

    def point(self, tick):
        if tick in self.timeline.tick_list:
            return TimelinePoint(self, tick)
        else:
            raise ValueError('Cannot create point: tick not in timeline tick list')

    def head_point(self):
        return TimelinePoint(self, self.timeline.head())

    def points(self):
        for tick in self.timeline.tick_list:
            yield TimelinePoint(self, tick)

    def __lt__(self, other):
        self_head = self.timeline.head()
        other_head = other.timeline.head()
        self_id = self.timeline_id
        other_id = other.timeline_id
        return (self_head < other_head
                or (
                        self_head == other_head
                        and self_id < other_id
                ))

    __le__ = __lt__

    def __gt__(self, other):
        self_head = self.timeline.head()
        other_head = other.timeline.head()
        self_id = self.timeline_id
        other_id = other.timeline_id
        return (self_head > other_head
                or (
                        self_head == other_head
                        and self_id > other_id
                ))

    __ge__ = __gt__


@dataclass(frozen=True)
class TimelinePoint:
    __slots__ = ('timeline_node', 'tick')
    timeline_node: TimelineNode
    tick: int

    def point_file_path(self):
        return self.timeline_node.timeline.get_point_file_path(self.tick)

    def timeline_id(self):
        return self.timeline_node.timeline_id

    def timeline(self):
        return self.timeline_node.timeline


class SimulationSource:
    AM_GIT_ARCHIVE_WORKING = 'git-archive-working'

    def __init__(self, source_file_path):
        self.source_file_path = Path(source_file_path).resolve(True)

        try:
            with open(self.source_file_path) as f:
                data = json.load(f)

            self.name = data['name']
            self.binary = data['binary']
            self.archive_method = data['archive_method']
        except (LookupError, json.JSONDecodeError):
            raise ValueError('Source file not formatted correctly.')

        if self.archive_method not in [SimulationSource.AM_GIT_ARCHIVE_WORKING]:
            raise ValueError('Bad archive method in simulation source file.')

    def __str__(self):
        return f"Source: {self.source_file_path}"

    def get_json(self):
        with open(self.source_file_path) as f:
            data = json.load(f)
            return json.dumps(data, indent=4)

    def get_simulation_binary_name(self):
        return Path(self.binary).name

    def get_simulation_binary_path(self):
        return (self.source_file_path.parent / self.binary).resolve(False)


class SimulationRegistration:
    @staticmethod
    def create_registration(parent_folder: Path, uuid: UUID, name: str, binary_name: str, created_from: str,
                            description: str):
        registration_folder = parent_folder / str(uuid)
        registration_folder.mkdir()

        registration = SimulationRegistration(registration_folder)

        registration.get_bin_path().mkdir()
        registration.get_src_path().mkdir()

        meta = {
            'name': name,
            'binary': binary_name,
            'created_from': created_from,
            'creation_date': str(datetime.today())
        }

        with open(str(registration.get_metadata_file_path()), "w") as mf:
            json.dump(meta, mf)

        with open(str(registration.get_description_file_path()), "w") as df:
            df.write(description)

        return registration

    def __init__(self, path):
        self.path: Path = Path(path).resolve(True)
        self.uuid = UUID(self.path.name)

    def __str__(self):
        return f"Registration: {self.uuid}"

    def get_metadata_file_path(self):
        return self.path / "metadata.json"

    def get_description_file_path(self):
        return self.path / "description.txt"

    def get_bin_path(self):
        return self.path / "bin"

    def get_src_path(self):
        return self.path / "src"

    def get_metadata(self):
        with open(str(self.get_metadata_file_path())) as f:
            return json.load(f)

    def get_metadata_json(self):
        return json.dumps(self.get_metadata(), indent=4)

    def get_description(self):
        with open(str(self.get_description_file_path())) as f:
            return f.read()

    def set_description(self, description):
        with open(str(self.get_description_file_path()), "w") as f:
            f.write(description)

    def get_simulation_binary_path(self):
        metadata = self.get_metadata()
        binary_path = Path(metadata['binary'])
        if len(binary_path.parts) != 1:
            raise RuntimeError("Simulation registry binary name is not valid.")
        return (self.get_bin_path() / binary_path).resolve(True)


class TimelinesProject:
    @staticmethod
    def create_new_project(project_root_dir):
        project = TimelinesProject(project_root_dir)

        project.root_dir_path.mkdir()
        with project.project_file_path.open('x') as project_file:
            json.dump({}, project_file)

        project._project_file_handle = project.project_file_path.open('r+')

        return project

    @staticmethod
    def load_project(project_root_dir):
        project = TimelinesProject(project_root_dir)

        project._project_file_handle = project.project_file_path.open('r+')

        project.load_all_simulation_sources()
        project.load_simulation_registry()
        project.load_all_timelines()

        return project

    @staticmethod
    def timeline_folder_name(timeline_id: int, parent_timeline_id: Optional[int]):
        if parent_timeline_id is not None:
            return f't{timeline_id}_p{parent_timeline_id}'
        else:
            return f't{timeline_id}'

    @staticmethod
    def parse_timeline_folder_name(folder_name):
        exp = re.compile(r'^t(?P<timeline_id>\d+)(_p(?P<parent_timeline_id>\d+))?$')
        result = exp.match(folder_name)
        if result:
            timeline_id = result.group('timeline_id')
            parent_timeline_id = result.group('parent_timeline_id')
            timeline_id = int(timeline_id)
            parent_timeline_id = int(parent_timeline_id) if parent_timeline_id else None
            return timeline_id, parent_timeline_id
        else:
            return None, None

    def __init__(self, project_root_dir):
        self.root_dir_path = Path(project_root_dir).resolve()
        self.timelines_dir_path = self.root_dir_path / 'timelines'
        self.project_file_path = self.root_dir_path / 'timelines.project'
        self.simulation_registry_path = self.root_dir_path / 'sim_registry'
        self.project_file_handle = None
        self.root_node = TimelineNode()
        self._next_new_timeline_id = 1
        self._timeline_nodes = {}
        self._simulation_source_paths = []
        self._simulation_registry = {}

    def _create_timeline(self,
                         parent_node: TimelineNode,
                         sim_binary_provider=None,
                         initial_tick=0,
                         source_tick_data_path=None):
        new_timeline_id = self._next_new_timeline_id

        timeline_folder_name = TimelinesProject.timeline_folder_name(new_timeline_id, parent_node.timeline_id)
        timeline_folder_path = self.timelines_dir_path / timeline_folder_name

        try:
            timeline_folder_path.mkdir()

            new_timeline = Timeline(timeline_folder_path, sim_binary_provider)
            self._save_timeline(new_timeline)

            initial_point_path = new_timeline.get_point_file_path(initial_tick)

            if source_tick_data_path is not None:
                shutil.copy(str(source_tick_data_path), str(initial_point_path))
            elif sim_binary_provider is not None:
                sim_path = str(sim_binary_provider.get_simulation_binary_path())
                SimulationProcess.create_default(str(initial_point_path), "binary", sim_path)
            else:
                initial_point_path.touch(exist_ok=False)

            new_timeline.refresh_tick_list()
        except Exception:
            shutil.rmtree(timeline_folder_path)
            raise

        new_timeline_node = TimelineNode(parent_node, new_timeline_id, new_timeline)
        self._timeline_nodes[new_timeline_id] = new_timeline_node
        self._next_new_timeline_id += 1
        return new_timeline_node

    def create_timeline(self, derive_from: Optional[TimelinePoint] = None):
        if derive_from is None:
            return self._create_timeline(self.root_node)
        else:
            return self._create_timeline(derive_from.timeline_node,
                                         derive_from.timeline().simulation_binary_provider,
                                         derive_from.tick,
                                         derive_from.point_file_path())

    def clone_timeline(self, node_to_clone: TimelineNode):
        return self._create_timeline(node_to_clone.parent_node,
                                     node_to_clone.timeline.simulation_binary_provider,
                                     node_to_clone.head_point().tick,
                                     node_to_clone.head_point().point_file_path())

    def delete_timeline(self, node_to_delete: TimelineNode):
        """
        Deletes all timeline data of the given node AND all its children.
        :param node_to_delete: Node to delete
        :return:
        """
        from shutil import rmtree
        timelines_dir = self.timelines_dir_path.resolve(True)

        def delete_timeline_data(node):
            nonlocal timelines_dir
            path: Path = node.timeline.path.resolve(True)
            if path.parent == timelines_dir:
                rmtree(path)
            else:
                print(f"Attempted to delete a timeline that is not part of this project. Node will be removed, "
                      f"but data on disk will remain. ({path})", file=sys.stderr)
            del self._timeline_nodes[node.timeline_id]

        TimelineNode.traverse(node_to_delete, delete_timeline_data)
        node_to_delete.parent_node.child_nodes.remove(node_to_delete)
        node_to_delete.parent_node = None

        max_id = 0

        def find_max_id(node: TimelineNode):
            nonlocal max_id
            if node.timeline_id is not None:
                max_id = max(max_id, node.timeline_id)

        TimelineNode.traverse(self.root_node, find_max_id)
        self._next_new_timeline_id = max_id + 1

    def load_all_timelines(self):
        timeline_nodes = {}
        timeline_children = defaultdict(list)
        largest_loaded_timeline_id = 0

        # pass 1: load all timelines individually, and log parent timelines+ticks
        for timeline_path in (p for p in self.timelines_dir_path.iterdir() if p.is_dir()):
            timeline_id, parent_id = TimelinesProject.parse_timeline_folder_name(timeline_path.name)
            if timeline_id is None:
                print(f"WARNING: Improperly formatted folder found in timelines dir '{timeline_path.name}'.")
                continue

            timeline = self._load_timeline(timeline_path)

            timeline_children[parent_id].append((timeline_id, timeline))
            largest_loaded_timeline_id = max(largest_loaded_timeline_id, timeline_id)

        # pass 2: Starting at the root, populate tree with nodes
        root_node = TimelineNode()
        node_deque = deque([root_node])

        while node_deque:
            cur_node = node_deque.popleft()
            timeline_nodes[cur_node.timeline_id] = cur_node
            for timeline_id, timeline in timeline_children[cur_node.timeline_id]:
                child_node = TimelineNode(cur_node, timeline_id, timeline)
                node_deque.append(child_node)
            del timeline_children[cur_node.timeline_id]

        if len(timeline_children) > 0:
            print(f"WARNING: Some timelines are not attached to the root point and have not been loaded.")
            print(timeline_children)

        self.root_node = root_node
        self._timeline_nodes = timeline_nodes
        self._next_new_timeline_id = largest_loaded_timeline_id + 1

    def get_timeline_node(self, timeline_id) -> TimelineNode:
        return self._timeline_nodes[timeline_id]

    def load_all_simulation_sources(self):
        self._simulation_source_paths = []
        sources_file_path = self.simulation_registry_path / 'sources.txt'
        self.simulation_registry_path.mkdir(exist_ok=True)
        sources_file_path.touch(exist_ok=True)
        with open(sources_file_path) as sf:
            for line in sf.readlines():
                line = line.strip()
                if line:
                    try:
                        path = Path(line)
                        SimulationSource(path)
                        self._simulation_source_paths.append(path)
                    except (ValueError, FileNotFoundError):
                        print(f"Failed to load source {line}.")

    def get_simulation_source_paths(self):
        yield from self._simulation_source_paths

    def add_simulation_source_path(self, source_path):
        source_path = Path(source_path).resolve(True)
        if source_path in self._simulation_source_paths:
            raise ValueError("Source path already in sources list.")
        SimulationSource(source_path)  # validate that path is a valid source

        with open(self.simulation_registry_path / 'sources.txt', 'ba+') as f:
            if f.tell() != 0:
                f.seek(-1, 2)
                last_char = f.read(1)
                if last_char != b'\n':
                    f.write(os.linesep.encode('utf-8'))
            f.write(str(source_path).encode('utf-8'))
            f.write(os.linesep.encode('utf-8'))

        self._simulation_source_paths.append(source_path)

    def remove_simulation_source_path(self, source_path):
        source_path = Path(source_path).resolve(True)
        self._simulation_source_paths.remove(source_path)

        with open(self.simulation_registry_path / 'sources.txt', 'w') as f:
            f.writelines((str(p) for p in self._simulation_source_paths))

    def load_simulation_registry(self):
        self._simulation_registry = {}
        for dir_path in (x for x in self.simulation_registry_path.iterdir() if x.is_dir()):
            try:
                reg_id = UUID(dir_path.name)
            except ValueError:
                print(f"Bad registered simulation UUID: {dir_path.name}")
                continue

            if reg_id in self._simulation_registry:
                print(f"Registered simulation appears twice with the same UUID {reg_id}")
                continue

            self._simulation_registry[reg_id] = SimulationRegistration(dir_path)

    def get_registered_simulations(self):
        yield from self._simulation_registry.values()

    def get_registered_simulation(self, uuid) -> SimulationRegistration:
        return self._simulation_registry[uuid]

    def register_simulation(self, source: SimulationSource, description=""):
        uuid = uuid4()
        while uuid in self._simulation_registry:
            # duplicate prevention
            uuid = uuid4()

        registration = SimulationRegistration.create_registration(
            self.simulation_registry_path,
            uuid,
            source.name,
            source.get_simulation_binary_name(),
            str(source.source_file_path),
            description
        )

        try:
            # after creating the registration, need to copy over the binaries + code
            binary_path = source.get_simulation_binary_path().resolve(True)
            shutil.copy2(str(binary_path), str(registration.get_bin_path()))

            # copying code depends on the archive method
            dst_source_path = registration.get_src_path()
            if source.archive_method == SimulationSource.AM_GIT_ARCHIVE_WORKING:
                archive_path = dst_source_path / 'code.tar.gz'
                git = subprocess.Popen(('git', 'ls-files', '-o', '-c', '--exclude-standard'),
                                       cwd=source.source_file_path.parent,
                                       stdout=subprocess.PIPE)
                subprocess.run(('tar', 'T', '-', '-czf', str(archive_path)),
                               cwd=source.source_file_path.parent,
                               stdin=git.stdout,
                               check=True)
                if git.wait():
                    raise RuntimeError("git encountered an error.")
            else:
                raise ValueError(f"Source file has unknown archive method: {source.archive_method}")

            self._simulation_registry[uuid] = registration
        except Exception:
            shutil.rmtree(registration.path)
            raise

        return registration

    def unregister_simulation(self, uuid):
        registration = self._simulation_registry[uuid]
        if registration.path.parent != self.simulation_registry_path:
            raise RuntimeError("Cannot unregister: registration path is not within simulation registry.")

        def node_has_registry(node: TimelineNode):
            if node.timeline is not None and node.timeline.simulation_binary_provider is registration:
                return True
            else:
                return None

        timeline_has_registration = TimelineNode.traverse(self.root_node, node_has_registry)
        if timeline_has_registration:
            raise RuntimeError("Cannot unregister: a timeline is currently using this registration.")

        shutil.rmtree(registration.path)
        del self._simulation_registry[uuid]

    def create_timeline_simulation(self, timeline_id):
        node = self.get_timeline_node(timeline_id)
        return TimelineSimulation(node.timeline)

    def change_timeline_simulation_provider(self, timeline_id, new_simulation_provider):
        node = self.get_timeline_node(timeline_id)
        head_point = node.head_point()
        timeline = node.timeline

        if timeline.simulation_binary_provider is None:
            head_point_path = head_point.point_file_path().resolve(False)
            new_sim_path = str(new_simulation_provider.get_simulation_binary_path())
            SimulationProcess.create_default(str(head_point_path), "binary", new_sim_path)
            timeline.simulation_binary_provider = new_simulation_provider
            self._save_timeline(timeline)
        else:
            head_point_path = head_point.point_file_path().resolve(True)
            backup_path = head_point_path.with_suffix('.tmp')

            try:
                shutil.copy2(str(head_point_path), str(backup_path))
                old_sim_path = str(timeline.get_simulation_binary_path())
                new_sim_path = str(new_simulation_provider.get_simulation_binary_path())
                SimulationProcess.simple_convert(str(backup_path), "binary", old_sim_path,
                                                 str(head_point_path), "binary", new_sim_path)

                timeline.simulation_binary_provider = new_simulation_provider
                self._save_timeline(timeline)
            except Exception:
                shutil.copy2(str(backup_path), str(head_point_path))
                raise
            finally:
                Path(backup_path).unlink()

    def get_all_simulation_providers(self):
        for source in self.get_simulation_source_paths():
            yield SimulationSource(source)
        yield from self.get_registered_simulations()

    def get_all_timeline_nodes(self):
        return self._timeline_nodes.values()

    def get_timeline_events(self, timeline_id, *, start_tick=None, end_tick=None, filters=None):
        """

        :param timeline_id:
        :param start_tick:
        :param end_tick:
        :param filters:
        :return: A list of (tick, event_name, event_json) tuples, containing the requested event data.
        Events will be returned in ascending tick order, with no guarantee that events within a single tick
        will be consistently ordered
        """
        node = self.get_timeline_node(timeline_id)

        query = "SELECT tick, event_name, event_json FROM events"
        where_clauses = []
        parameters = []

        if start_tick is not None:
            where_clauses.append("tick >= ?")
            parameters.append(start_tick)

        if end_tick is not None:
            where_clauses.append("tick <= ?")
            parameters.append(end_tick)

        if filters:
            filter_clauses = []
            filter_parameters = []
            for f in filters:
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

        db_conn = node.timeline.get_db_conn()

        cursor = db_conn.execute(query, tuple(parameters))

        row = cursor.fetchone()
        events = []

        while row is not None:
            events.append(tuple(row))
            row = cursor.fetchone()

        return events

    def _save_timeline(self, timeline: Timeline):
        if timeline.path.parent != self.timelines_dir_path:
            raise ValueError("Provided timeline node has invalid path data")

        timeline_config_path = (timeline.path / 'timeline.json').resolve()
        data = {}
        sim_binary_provider = timeline.simulation_binary_provider
        with timeline_config_path.open('w') as f:
            if isinstance(sim_binary_provider, SimulationRegistration):
                data['simulation_uuid'] = str(timeline.simulation_binary_provider.uuid)
            elif isinstance(sim_binary_provider, SimulationSource):
                data['source_path'] = str(sim_binary_provider.source_file_path)
            json.dump(data, f)

    def _load_timeline(self, timeline_path):
        if timeline_path.parent != self.timelines_dir_path:
            raise ValueError("Provided timeline path is not part of project")

        timeline_config_path = (timeline_path / 'timeline.json').resolve(True)
        with timeline_config_path.open('r') as f:
            data = json.load(f)

            if 'simulation_uuid' in data and 'source_path' in data:
                raise ValueError("Timeline configured with both simulation uuid and source path.")

            if 'simulation_uuid' in data:
                uuid = UUID(data['simulation_uuid'])
                simulation_binary_provider = self.get_registered_simulation(uuid)
            elif 'source_path' in data:
                source_path = Path(data['source_path'])
                if source_path not in self._simulation_source_paths:
                    raise ValueError("Timeline configured with source path that isn't part of the project.")
                simulation_binary_provider = SimulationSource(source_path)
            else:
                simulation_binary_provider = None

        return Timeline(timeline_path, simulation_binary_provider)
