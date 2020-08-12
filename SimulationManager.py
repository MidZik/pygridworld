"""
@author: Matt Idzik (MidZik)
"""
from collections import defaultdict, deque
from pathlib import Path
import json
import re
from typing import Optional
from bisect import insort
from simrunner import SimulationProcess
from timeline import Timeline
from dataclasses import dataclass
import sys
from datetime import datetime
from uuid import uuid4, UUID
import shutil
import subprocess
import os


class TimelineSimulation:
    """
    Manages a SimulationRunnerProcess associated with a timeline.
    """
    def __init__(self, timeline, simulation_binary_path):
        self.timeline: Timeline = timeline
        self.simulation_binary_path = simulation_binary_path

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

        sim_state_json = self.get_state_json()
        head_point_path = self.timeline.get_point_file_path(self.timeline.head())
        with head_point_path.open('w') as f:
            f.write(sim_state_json)

        self._is_editing = False

    def discard_edits(self):
        """
        Revert the simulation state to the head point and exit edit mode.
        """
        if not self._is_editing:
            raise RuntimeError("Cannot discard edits: not in edit mode.")

        head_point_path = self.timeline.get_point_file_path(self.timeline.head())
        with head_point_path.open('r') as f:
            self.set_state_json(f.read())

        self._is_editing = False

    def move_to_tick(self, tick: int):
        if tick not in self.timeline.tick_list:
            raise ValueError('Point tick is not part of simulation timeline.')

        if self._is_editing:
            raise RuntimeError('Cannot move to point while simulation is being edited.')

        if self.is_running():
            raise RuntimeError('Cannot move to point while simulation is running.')

        with self.timeline.get_point_file_path(tick).open('r') as f:
            self._simulation_process.get_client().set_state_json(f.read())

    def start_process(self, initial_tick=None):
        if initial_tick is None:
            initial_tick = self.timeline.head()
        elif initial_tick not in self.timeline.tick_list:
            raise ValueError('Attempted to start timeline simulation at an invalid tick.')

        self._simulation_process = SimulationProcess(
            self.simulation_binary_path,
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

    def _handle_event(self, tick, event_json, state_json):
        if tick not in self.timeline.tick_list:
            state_file_path = self.timeline.get_point_file_path(tick)
            with state_file_path.open('w') as state_file:
                state_file.write(state_json)
            self.timeline.tick_list.append(tick)


class TimelineNode:
    @staticmethod
    def traverse(root_node: 'TimelineNode', callback):
        traversal_deque = deque([root_node])
        while traversal_deque:
            cur_node = traversal_deque.pop()
            callback(cur_node)
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

    def get_json(self):
        with open(self.source_file_path) as f:
            data = json.load(f)
            return json.dumps(data, indent=4)

    def get_binary_name(self):
        return Path(self.binary).name

    def get_binary_path(self):
        return (self.source_file_path.parent / self.binary).resolve(False)


class SimulationRegistration:
    @staticmethod
    def create_registration(registration_folder: Path, name: str, binary_name: str, created_from: str, description: str):
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


@dataclass(frozen=True)
class TimelineSimulationConfig:
    __slots__ = ('uuid', 'source')
    uuid: Optional[UUID]
    source: Optional[Path]

    def __str__(self):
        if self.uuid is not None:
            return "UUID: " + str(self.uuid)
        elif self.source is not None:
            return "Source: " + str(self.source)
        else:
            return "No Config"


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

        project.load_all_timelines()
        project.load_all_simulation_sources()
        project.load_simulation_registry()
        project._project_file_handle = project.project_file_path.open('r+')

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

    def create_timeline(self, derive_from: Optional[TimelinePoint] = None):
        new_timeline_id = self._next_new_timeline_id

        if derive_from is None:
            derive_from_node = self.root_node
            derive_from_tick = None
        else:
            derive_from_node = derive_from.timeline_node
            derive_from_tick = derive_from.tick

        timeline_folder_name = TimelinesProject.timeline_folder_name(new_timeline_id, derive_from_node.timeline_id)
        timeline_folder_path = self.timelines_dir_path / timeline_folder_name

        new_timeline = Timeline.create_timeline(timeline_folder_path, derive_from_node.timeline, derive_from_tick)
        new_timeline_node = TimelineNode(derive_from_node, new_timeline_id, new_timeline)
        self._next_new_timeline_id += 1
        return new_timeline_node

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

            timeline = Timeline(timeline_path)

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
        yield from self._simulation_registry.items()

    def get_registered_simulation(self, uuid) -> SimulationRegistration:
        return self._simulation_registry[uuid]

    def register_simulation(self, source: SimulationSource, description=""):
        uuid = uuid4()
        while uuid in self._simulation_registry:
            # duplicate prevention
            uuid = uuid4()

        registration_path = self.simulation_registry_path / str(uuid)
        registration = SimulationRegistration.create_registration(
            registration_path,
            source.name,
            source.get_binary_name(),
            str(source.source_file_path),
            description
        )

        try:
            # after creating the registration, need to copy over the binaries + code
            binary_path = source.get_binary_path().resolve(True)
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

        return uuid, registration

    def unregister_simulation(self, uuid):
        registration = self._simulation_registry[uuid]
        if registration.path.parent != self.simulation_registry_path:
            raise RuntimeError("Cannot unregister: registration path is not within simulation registry.")
        shutil.rmtree(registration.path)
        del self._simulation_registry[uuid]

    def create_timeline_simulation(self, timeline_id):
        node = self.get_timeline_node(timeline_id)
        timeline = node.timeline
        if timeline.config.simulation_uuid is not None:
            reg = self.get_registered_simulation(timeline.config.simulation_uuid)
            sim_path = reg.get_simulation_binary_path()
        else:
            source = SimulationSource(timeline.config.source_path)
            sim_path = source.get_binary_path()
        return TimelineSimulation(timeline, sim_path)

    def change_timeline_simulation_uuid(self, timeline_id, uuid):
        timeline = self.get_timeline_node(timeline_id).timeline
        if uuid != timeline.config.simulation_uuid:
            timeline.config.simulation_uuid = uuid
            timeline.config.source_path = None
            timeline.save()

    def change_timeline_simulation_path(self, timeline_id, path):
        timeline = self.get_timeline_node(timeline_id).timeline
        if path != timeline.config.source_path:
            timeline.config.simulation_uuid = None
            timeline.config.source_path = path
            timeline.save()

    def get_timeline_simulation_configs(self):
        for source in self.get_simulation_source_paths():
            yield TimelineSimulationConfig(None, source)
        for uuid, reg in self.get_registered_simulations():
            yield TimelineSimulationConfig(uuid, None)

    def get_timeline_simulation_config_from_timeline(self, timeline_id):
        node = self.get_timeline_node(timeline_id)
        timeline = node.timeline
        sim_uuid = timeline.config.simulation_uuid
        if sim_uuid is not None:
            return self.get_timeline_simulation_config_from_uuid(sim_uuid)
        else:
            return self.get_timeline_simulation_config_from_source(timeline.config.source_path)

    def get_timeline_simulation_config_from_uuid(self, uuid):
        reg = self.get_registered_simulation(uuid)
        return TimelineSimulationConfig(uuid, reg.get_simulation_binary_path())

    def get_timeline_simulation_config_from_source(self, source_path):
        if source_path not in self._simulation_source_paths:
            return None

        return TimelineSimulationConfig(None, source_path)
