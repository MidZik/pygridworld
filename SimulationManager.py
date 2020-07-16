"""
@author: Matt Idzik (MidZik)
"""
from collections import defaultdict, deque
import multiprocessing
from multiprocessing.connection import Connection, Listener, wait
from threading import Thread
from pathlib import Path
import json
import re
from typing import Optional
from bisect import insort
from simrunner import SimulationRunnerProcess
from timeline import Timeline
from dataclasses import dataclass
import sys


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
        ctrl = self._simulation_process.controller
        return (timeline.head() == timeline.tail() and
                ctrl.get_tick() == timeline.head() and
                not ctrl.is_running() and
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
            self._simulation_process.controller.set_state_json(f.read())

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
        self._simulation_process.controller.stop_process()
        self._simulation_process.join_process()
        self._simulation_state_queue.put(None)
        self._handle_queue_thread.join()
        self._handle_queue_thread = None

    def start_simulation(self):
        if not self._is_editing:
            self._simulation_process.controller.start_simulation()

    def stop_simulation(self):
        self._simulation_process.controller.stop_simulation()

    def is_running(self):
        return self._simulation_process.controller.is_running()

    def get_tick(self):
        return self._simulation_process.controller.get_tick()

    def get_state_json(self):
        return self._simulation_process.controller.get_state_json()

    def set_state_json(self, state_json):
        if self._is_editing:
            self._simulation_process.controller.set_state_json(state_json)

    def create_entity(self):
        if self._is_editing:
            return self._simulation_process.controller.create_entity()

    def destroy_entity(self, eid):
        if self._is_editing:
            self._simulation_process.controller.destroy_entity(eid)

    def get_all_entities(self):
        return self._simulation_process.controller.get_all_entities()

    def assign_component(self, eid, com_name):
        if self._is_editing:
            self._simulation_process.controller.assign_component(eid, com_name)

    def get_component_json(self, eid, com_name):
        return self._simulation_process.controller.get_component_json(eid, com_name)

    def remove_component(self, eid, com_name):
        if self._is_editing:
            self._simulation_process.controller.remove_component(eid, com_name)

    def replace_component(self, eid, com_name, state_json):
        if self._is_editing:
            self._simulation_process.controller.replace_component(eid, com_name, state_json)

    def get_component_names(self):
        return self._simulation_process.controller.get_component_names()

    def get_entity_component_names(self, eid):
        return self._simulation_process.controller.get_entity_component_names(eid)

    def get_singleton_json(self, singleton_name):
        return self._simulation_process.controller.get_singleton_json(singleton_name)

    def set_singleton_json(self, singleton_name, singleton_json):
        if self._is_editing:
            self._simulation_process.controller.set_singleton_json(singleton_name, singleton_json)

    def get_singleton_names(self):
        return self._simulation_process.controller.get_singleton_names()

    def new_controller(self):
        return self._simulation_process.controller.new_controller()

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
        self.project_file_handle = None
        self.root_node = TimelineNode()
        self._next_new_timeline_id = 1
        self._timeline_nodes = {}

        self.server_thread = Thread(target=self.start_project_server)
        self.server_thread.start()

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

    def get_timeline_node(self, timeline_id):
        return self._timeline_nodes[timeline_id]

    def start_project_server(self):
        def request_handler(connection: Connection):
            while True:
                try:
                    cmd, params = connection.recv()
                    if cmd == "get_ticks":
                        timeline_id, = params
                        node = self._timeline_nodes[timeline_id]
                        connection.send((True, node.timeline.tick_list))
                    if cmd == "get_state":
                        timeline_id, tick = params
                        point: TimelinePoint = self._timeline_nodes[timeline_id].point(tick)
                        with point.point_file_path().open('r') as point_file:
                            connection.send((True, point_file.read()))
                except (EOFError, ConnectionError):
                    break
                except Exception as e:
                    connection.send((False, None))

        request_thread = Thread(target=request_handler)
        listener = Listener(('127.0.0.1', 4969), authkey=b'local-timelines-project-server')

        while True:
            try:
                new_con = listener.accept()
                new_request_thread = Thread(target=request_handler, args=(new_con,))
                new_request_thread.start()
            except multiprocessing.context.AuthenticationError:
                pass
