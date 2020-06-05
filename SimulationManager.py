"""
@author: Matt Idzik (MidZik)
"""
from collections import defaultdict, deque
import multiprocessing
from threading import Lock, Thread
from pathlib import Path
import json
import re
import shutil
from typing import Optional, List
from bisect import insort
from simrunner import SimulationRunnerProcess


class TimelineConfig:
    @staticmethod
    def create_from_path(path):
        config = TimelineConfig()
        config.load_from(path)
        return config

    def __init__(self):
        self.simulation_path: Optional[Path] = None

    def load_from(self, path):
        path = Path(path).resolve(True)
        with path.open('r') as f:
            data = json.load(f)
            simulation_path = data['simulation_path']
            if simulation_path is not None:
                self.simulation_path = Path(simulation_path)

    def save_to(self, path):
        path = Path(path).resolve(True)
        with path.open('w') as f:
            simulation_path = str(self.simulation_path) if self.simulation_path else None
            data = {
                'simulation_path': simulation_path
            }
            json.dump(data, f)


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

    @staticmethod
    def create_timeline(path: Path, derive_from: Optional['Timeline'], derive_from_tick: Optional[int]):
        """
        Create and return a new timeline at a given location.
        :param path: The folder that the timeline should be created in. (Must not exist)
        :param derive_from: The timeline this timeline should be derived from
        :param derive_from_tick: If derived from a timeline, the tick at which it should be derived from
        :return: The newly created timeline.
        """
        path.mkdir()

        if derive_from is not None:
            derive_from.config.save_to(path / 'timeline.json')
            derive_from_tick = derive_from_tick if derive_from_tick is not None else derive_from.point_tick_list[0]
            derive_from_point_path = derive_from.get_point_file_path(derive_from_tick)
            new_point_path = path / Timeline.point_file_name(derive_from_tick)
            shutil.copyfile(str(derive_from_point_path), new_point_path)
        else:
            config = TimelineConfig()
            config.save_to(path / 'timeline.json')

        return Timeline(path)

    def __init__(self, path: Path):
        """
        :param path: The folder the timeline data resides in.
        """
        self.path: Path = path.resolve(True)
        self.config: TimelineConfig = TimelineConfig.create_from_path(self.get_config_file_path())

        self.tick_list: List[int] = []

        for point_path in self.path.glob('*.point'):
            tick = Timeline.parse_point_file_name(point_path.name)
            if tick is not None:
                self.tick_list.append(tick)

        self.tick_list.sort()

    def get_point_file_path(self, tick):
        return self.path / Timeline.point_file_name(tick)

    def get_config_file_path(self):
        return self.path / 'timeline.json'

    def save_config(self):
        self.config.save_to(self.get_config_file_path())

    def head(self):
        return self.tick_list[0]

    def tail(self):
        return self.tick_list[-1]


class TimelineSimulation:
    """
    Manages a SimulationRunnerProcess associated with a timeline.
    """
    def __init__(self, timeline, working_dir):

        self.timeline: Timeline = timeline

        self._simulation_state_queue = multiprocessing.Queue(1000)

        self._process_working_dir = Path(working_dir).resolve()
        self._process_working_dir.mkdir(exist_ok=True)

        self._simulation_process: Optional[SimulationRunnerProcess] = None

        self._handle_queue_thread: Optional[Thread] = None

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
        sim = self._simulation_process
        return (timeline.head() == timeline.tail() and
                sim.get_tick() == timeline.head() and
                not sim.is_running() and
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
            self._simulation_process.set_state_json(f.read())

    def start_process(self, initial_tick=None):
        if initial_tick is None:
            initial_tick = self.timeline.head()
        elif initial_tick not in self.timeline.tick_list:
            raise ValueError('Attempted to start timeline simulation at an invalid tick.')

        self._simulation_process = SimulationRunnerProcess(
            self.timeline.config.simulation_path,
            self._process_working_dir,
            self._simulation_state_queue)
        self._simulation_process.start_process()

        self.move_to_tick(initial_tick)

        self._handle_queue_thread = Thread(target=self._handle_queue, daemon=False)
        self._handle_queue_thread.start()

    def stop_process(self):
        self._simulation_process.stop_and_join_process()
        self._simulation_state_queue.put(None)
        self._handle_queue_thread.join()
        self._handle_queue_thread = None

    def start_simulation(self):
        if not self._is_editing:
            self._simulation_process.start_simulation()

    def stop_simulation(self):
        self._simulation_process.stop_simulation()

    def is_running(self):
        return self._simulation_process.is_running()

    def get_tick(self):
        return self._simulation_process.get_tick()

    def get_state_json(self):
        return self._simulation_process.get_state_json()

    def set_state_json(self, state_json):
        if self._is_editing:
            self._simulation_process.set_state_json(state_json)

    def create_entity(self):
        if self._is_editing:
            return self._simulation_process.create_entity()

    def destroy_entity(self, eid):
        if self._is_editing:
            self._simulation_process.destroy_entity(eid)

    def get_all_entities(self):
        return self._simulation_process.get_all_entities()

    def assign_component(self, eid, com_name):
        if self._is_editing:
            self._simulation_process.assign_component(eid, com_name)

    def get_component_json(self, eid, com_name):
        return self._simulation_process.get_component_json(eid, com_name)

    def remove_component(self, eid, com_name):
        if self._is_editing:
            self._simulation_process.remove_component(eid, com_name)

    def replace_component(self, eid, com_name, state_json):
        if self._is_editing:
            self._simulation_process.replace_component(eid, com_name, state_json)

    def get_component_names(self):
        return self._simulation_process.get_component_names()

    def get_entity_component_names(self, eid):
        return self._simulation_process.get_entity_component_names(eid)

    def _handle_queue(self):
        while True:
            queue_item = self._simulation_state_queue.get()

            if queue_item is None:
                break

            tick, state_file_path = queue_item
            state_file_path = Path(state_file_path).resolve(True)

            if tick <= self.timeline.tail():
                # discard already recorded states
                state_file_path.unlink()
            else:
                # create new point and move in its state
                state_file_path.rename(self.timeline.get_point_file_path(tick))
                self.timeline.tick_list.append(tick)


class TimelineTreeNode:
    def __init__(self,
                 parent_node: Optional['TimelineTreeNode'] = None,
                 timeline_id: Optional[int] = None,
                 timeline: Optional[Timeline] = None):
        self.parent_node = parent_node
        self.timeline_id = timeline_id
        self.timeline = timeline
        self.child_nodes = []

        if parent_node is not None:
            parent_node.insert_child(self)

    def insert_child(self, child: 'TimelineTreeNode'):
        insort(self.child_nodes, child)

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
        project._project_file_handle = project.project_file_path.open('r+')

        return project

    @staticmethod
    def timeline_folder_name(timeline_id, parent_timeline_id):
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
        self.project_file_handle = None
        self.root_node = TimelineTreeNode()
        self._next_new_timeline_id = 1
        self._timeline_nodes = {}

    def create_timeline(self, parent_node: Optional[TimelineTreeNode] = None, parent_tick: Optional[int] = None):
        new_timeline_id = self._next_new_timeline_id

        parent_node = parent_node if parent_node is not None else self.root_node

        timeline_folder_name = TimelinesProject.timeline_folder_name(new_timeline_id, parent_node.timeline_id)
        timeline_folder_path = self.timelines_dir_path / timeline_folder_name

        new_timeline = Timeline.create_timeline(timeline_folder_path, parent_node.timeline, parent_tick)
        new_timeline_node = TimelineTreeNode(parent_node, new_timeline_id, new_timeline)
        self._next_new_timeline_id += 1
        return new_timeline_node

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
        root_node = TimelineTreeNode()
        node_deque = deque([root_node])

        while node_deque:
            cur_node = node_deque.popleft()
            timeline_nodes[cur_node.timeline_id] = cur_node
            for timeline_id, timeline in timeline_children[cur_node.timeline_id]:
                child_node = TimelineTreeNode(cur_node, timeline_id, timeline)
                node_deque.append(child_node)
            del timeline_children[cur_node.timeline_id]

        if len(timeline_children) > 0:
            print(f"WARNING: Some timelines are not attached to the root point and have not been loaded.")
            print(timeline_children)

        self.root_node = root_node
        self._timeline_nodes = timeline_nodes
        self._next_new_timeline_id = largest_loaded_timeline_id + 1

    def get_timeline_node(self, timeline_id):
        return self._timeline_nodes[timeline_id]
