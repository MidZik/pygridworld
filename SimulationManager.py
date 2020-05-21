"""
@author: Matt Idzik (MidZik)
"""
from collections import defaultdict, deque
from importlib import util
from multiprocessing.connection import Connection
from multiprocessing import Pipe, Process
import multiprocessing
from threading import Lock, Thread
from pathlib import Path
import json
from datetime import datetime
import queue
import re
import shutil
from typing import Optional
import os


class SimulationRunner:
    def __init__(self, simulation_folder_path, runner_working_dir, state_file_written_callback=None):
        simulation_module_path = (simulation_folder_path / "simulation.pyd").resolve(True)
        spec = util.spec_from_file_location("simulation", simulation_module_path)
        self.module = util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

        self.simulation = self.module.Simulation()
        self.simulation.set_event_callback(self._on_simulation_event)

        self._working_dir = Path(runner_working_dir).resolve()
        self._saved_states_dir = (self._working_dir / 'saved_states').resolve()
        self._saved_states_dir.mkdir(exist_ok=True)
        self._logs_dir = (self._working_dir / 'logs').resolve()
        self._logs_dir.mkdir(exist_ok=True)
        self._cur_log_file = (self._logs_dir / f'log-{datetime.now():%Y-%m-%d}.txt').resolve()

        self._state_file_written_callback = state_file_written_callback

        self._state_jsons_to_save_queue = queue.Queue(100)
        self._state_writer_thread = Thread(target=self._queued_states_writer)
        self._state_writer_thread.start()

    def cleanup(self):
        # Shut off and join all threads
        self.simulation.stop_simulation()
        self._state_jsons_to_save_queue.put(None)
        self._state_jsons_to_save_queue.join()
        self._state_writer_thread.join()

    def start_simulation(self):
        self.simulation.start_simulation()

    def stop_simulation(self):
        self.simulation.stop_simulation()

    def is_running(self):
        """
        :return: True if the simulation is running, false otherwise.
        """
        return self.simulation.is_running()

    def get_tick(self):
        return self.simulation.get_tick()

    def get_state_json(self):
        return self.simulation.get_state_json()

    def set_state_json(self, state_json : str):
        self.simulation.set_state_json(state_json)

    def create_entity(self):
        return self.simulation.create_entity()

    def destroy_entity(self, eid):
        self.simulation.destroy_entity(eid)

    def assign_component(self, eid, com_name):
        self.simulation.assign_component(eid, com_name)

    def get_component_names(self):
        return self.simulation.get_component_names()

    def _on_simulation_event(self, events_json):
        events_obj = json.loads(events_json)
        self._state_jsons_to_save_queue.put(self.get_state_json())

    def _queued_states_writer(self):
        while True:
            try:
                state_json_to_write = self._state_jsons_to_save_queue.get(True, 1.0)
            except queue.Empty:
                continue

            try:
                if state_json_to_write is None:
                    break  # This is the sole exit condition for this loop
                else:
                    state_obj = json.loads(state_json_to_write)
                    tick = state_obj['singletons']['STickCounter']
                    if isinstance(tick, int):
                        state_file_path = (self._saved_states_dir / f'{tick}.json').resolve()
                        with state_file_path.open('w') as state_file:
                            state_file.write(state_json_to_write)
                        if self._state_file_written_callback is not None:
                            self._state_file_written_callback(tick, str(state_file_path))
                    else:
                        with self._cur_log_file.open('a') as log:
                            log.write(f'[{datetime.now():%H:%M:%S}] Could not write state, bad tick format: {tick}\n')
            except Exception as e:
                with self._cur_log_file.open('a') as log:
                    log.write(f'[{datetime.now():%H:%M:%S}] Unknown exception when writing state: {e}\n')
            finally:
                self._state_jsons_to_save_queue.task_done()


def simulation_runner_loop(con: Connection, simulation_folder_path, runner_working_dir, state_file_queue):
    def _on_state_file_written(tick, state_file_path):
        state_file_queue.put((tick, state_file_path))

    state_file_written_callback = _on_state_file_written if state_file_queue is not None else None

    runner = SimulationRunner(simulation_folder_path, runner_working_dir, state_file_written_callback)

    try:
        while True:
            try:
                cmd, params = con.recv()
                if cmd == "stop_process":
                    con.send((True, None))
                    break
                elif cmd == "start_simulation":
                    runner.start_simulation()
                    con.send((True, None))
                elif cmd == "stop_simulation":
                    runner.stop_simulation()
                    con.send((True, None))
                elif cmd == "is_running":
                    running = runner.is_running()
                    con.send((True, running))
                elif cmd == "get_tick":
                    tick = runner.get_tick()
                    con.send((True, tick))
                elif cmd == "get_state_json":
                    state_json = runner.get_state_json()
                    con.send((True, state_json))
                elif cmd == "set_state_json":
                    state_json, = params
                    runner.set_state_json(state_json)
                    con.send((True, None))
                elif cmd == "create_entity":
                    eid = runner.create_entity()
                    con.send((True, eid))
                elif cmd == "destroy_entity":
                    eid, = params
                    runner.destroy_entity(eid)
                    con.send((True, None))
                elif cmd == "assign_component":
                    eid, com_name = params
                    runner.assign_component(eid, com_name)
                    con.send((True, None))
                elif cmd == "get_component_names":
                    component_names = runner.get_component_names()
                    con.send((True, component_names))
                else:
                    con.send((False, f"Unknown command '{cmd}'."))
            except EOFError:
                # connection closed, end the simulation
                break
    finally:
        runner.cleanup()


class SimulationRunnerProcess:
    def __init__(self, simulation_folder_path, runner_working_dir, state_file_queue=None):
        self._conn, child_conn = Pipe()
        args = (child_conn, simulation_folder_path, runner_working_dir, state_file_queue)
        self._process = Process(target=simulation_runner_loop, args=args, daemon=True)
        self._lock = Lock()

    def start_process(self):
        self._process.start()

    def stop_and_join_process(self):
        self._send_command("stop_process")
        self._process.join()

    def start_simulation(self):
        self._send_command("start_simulation")

    def stop_simulation(self):
        self._send_command("stop_simulation")

    def is_running(self):
        return self._send_command("is_running")

    def get_tick(self):
        return self._send_command("get_tick")

    def get_state_json(self):
        return self._send_command("get_state_json")

    def set_state_json(self, state_json):
        self._send_command("set_state_json", state_json)

    def create_entity(self):
        return self._send_command("create_entity")

    def destroy_entity(self, eid):
        self._send_command("destroy_entity", eid)

    def assign_component(self, eid, com_name):
        self._send_command("assign_component", eid, com_name)

    def get_component_names(self):
        return self._send_command("get_component_names")

    def _send_command(self, command_str, *command_params):
        if not self._process.is_alive():
            raise RuntimeError("Unable to send command: process not running.")

        self._lock.acquire()
        self._conn.send((command_str, command_params))
        success, result = self._conn.recv()
        self._lock.release()
        if success:
            return result
        else:
            raise Exception(result)


class TimelinePoint:
    @staticmethod
    def create_file_name(tick):
        return f'tick-{tick}.point'

    @staticmethod
    def parse_file_name(file_name):
        exp = re.compile(r'^tick-(?P<tick>\d+)\.point$')
        result = exp.match(file_name)
        if result:
            return int(result.group('tick'))
        else:
            return None

    def __init__(self, tick, timeline):
        self.tick = tick

        self.timeline: Timeline = timeline
        self.derivative_timelines = []
        self.next_point: Optional[TimelinePoint] = None
        self.prev_point: Optional[TimelinePoint] = None

    def get_file_name(self):
        return TimelinePoint.create_file_name(self.tick)

    def get_file_path(self):
        if self.timeline is not None:
            return self.timeline.get_dir() / self.get_file_name()
        else:
            return None


class Timeline:
    @staticmethod
    def create_folder_name(timeline_id, parent_timeline_id):
        if parent_timeline_id is not None:
            return f't{timeline_id}_p{parent_timeline_id}'
        else:
            return f't{timeline_id}'

    @staticmethod
    def parse_folder_name(folder_name):
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

    @staticmethod
    def create_timeline(timelines_dir_path: Path, timeline_id: int, source_point: TimelinePoint):
        """
        Create and return a new timeline at a given location.
        :param timelines_dir_path: The folder that the timeline folder should be created in.
        :param timeline_id: The ID of the timeline.
        :param source_point: The point that the new timeline should derive from.
            Source point data will be copied into the new timeline head point.
        :return: The newly created timeline.
        """
        parent_timeline = source_point.timeline
        parent_timeline_id = parent_timeline.timeline_id if parent_timeline else None
        parent_simulation = parent_timeline.simulation_path if parent_timeline else None

        timeline = Timeline(timeline_id, parent_timeline_id, timelines_dir_path)
        timeline.simulation_path = parent_simulation

        timeline.get_dir().mkdir()

        head_point = TimelinePoint(source_point.tick, timeline)
        timeline.head_point = head_point
        timeline.tail_point = head_point

        if source_point.timeline is not None:
            shutil.copyfile(str(source_point.get_file_path()), head_point.get_file_path())
        else:
            with head_point.get_file_path().open('w') as head_point_file:
                json.dump({}, head_point_file)

        timeline.save_file()

        return timeline

    def __init__(self, timeline_id: int, parent_timeline_id: Optional[int], timelines_root_dir: Path):
        """
        :param timeline_id: The ID of the timeline
        :param parent_timeline_id: The ID of this timeline's parent timeline (if any).
        """
        self.timeline_id: int = timeline_id
        self.parent_timeline_id: Optional[int] = parent_timeline_id
        self._timelines_root_dir: Path = timelines_root_dir
        self.simulation_path: Optional[Path] = None
        self.head_point: Optional[TimelinePoint] = None
        self.tail_point: Optional[TimelinePoint] = None

    def get_folder_name(self):
        return Timeline.create_folder_name(self.timeline_id, self.parent_timeline_id)

    def get_dir(self):
        return self._timelines_root_dir / self.get_folder_name()

    def get_file_path(self):
        return self.get_dir() / 'timeline.json'

    def save_file(self):
        with self.get_file_path().open('w') as timeline_file:
            simulation_path = str(self.simulation_path) if self.simulation_path else None
            data = {
                'simulation_path': simulation_path
            }
            json.dump(data, timeline_file)

    def load_file(self):
        with self.get_file_path().open('r') as timeline_file:
            data = json.load(timeline_file)
            self.simulation_path = Path(data['simulation_path']).resolve(True)


class TimelineSimulation:
    def __init__(self, timeline, working_dir):

        self.timeline: Timeline = timeline

        self._simulation_state_queue = multiprocessing.Queue(1000)

        self._process_working_dir = Path(working_dir).resolve()
        self._process_working_dir.mkdir(exist_ok=True)

        self.simulation_process: Optional[SimulationRunnerProcess] = None

        self._handle_queue_thread = Thread(target=self._handle_queue, daemon=False)
        self._handle_queue_thread.start()

    def start_process(self):
        self.simulation_process = SimulationRunnerProcess(
            self.timeline.simulation_path,
            self._process_working_dir,
            self._simulation_state_queue)
        self.simulation_process.start_process()

    def stop_process(self):
        self.simulation_process.stop_and_join_process()

    def start_simulation(self):
        self.simulation_process.start_simulation()

    def stop_simulation(self):
        self.simulation_process.stop_simulation()

    def _handle_queue(self):
        while True:
            queue_item = self._simulation_state_queue.get()

            if queue_item is None:
                break

            tick, state_file_path = queue_item
            state_file_path = Path(state_file_path).resolve(True)

            if tick <= self.timeline.tail_point.tick:
                # discard already recorded states
                state_file_path.unlink()
            else:
                # create new point and move in its state
                prev_tail = self.timeline.tail_point
                new_point = TimelinePoint(tick, self.timeline)
                new_point.prev_point = prev_tail
                prev_tail.next_point = new_point
                self.timeline.tail_point = new_point
                state_file_path.rename(new_point.get_file_path())


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

    def __init__(self, project_root_dir):
        self.root_dir_path = Path(project_root_dir).resolve()
        self.timelines_dir_path = self.root_dir_path / 'timelines'
        self.project_file_path = self.root_dir_path / 'timelines.project'
        self.project_file_handle = None
        self.root_point = TimelinePoint(0, None)
        self._next_new_timeline_id = 1
        self._timelines = {}

    def create_timeline(self, source_point: Optional[TimelinePoint] = None):
        source_point = source_point if source_point is not None else self.root_point
        timeline = Timeline.create_timeline(self.timelines_dir_path, self._next_new_timeline_id, source_point)
        self._next_new_timeline_id += 1

        self.root_point.derivative_timelines.append(timeline)

        return timeline

    def create_timeline_simulation(self, timeline):
        working_dir = timeline.get_dir() / 'working'
        return TimelineSimulation(timeline, working_dir)

    def load_all_timelines(self):
        timelines = {}
        timeline_children = defaultdict(list)

        # pass 1: create all timelines and their points, and log parent timelines+ticks
        for timeline_path in (p for p in self.timelines_dir_path.iterdir() if p.is_dir()):
            timeline_id, parent_id = Timeline.parse_folder_name(timeline_path.name)
            if timeline_id is None:
                print(f"WARNING: Improperly formatted folder found in timelines dir '{timeline_path.name}'.")
                continue

            timeline = Timeline(timeline_id, parent_id, self.timelines_dir_path)
            timeline.load_file()
            ticks = []

            for point_path in timeline_path.glob('*.point'):
                tick = TimelinePoint.parse_file_name(point_path.name)
                if tick is not None:
                    ticks.append(tick)

            if len(ticks) <= 0:
                print(f"WARNING: Timeline {timeline_id} has no points. Skipped loading.")
                continue

            ticks = sorted(ticks)

            timeline.head_point = TimelinePoint(ticks[0], timeline)
            prev_point = timeline.head_point
            tail_point = timeline.head_point

            for tick in ticks[1:]:
                tail_point = TimelinePoint(tick, timeline)
                tail_point.prev_point = prev_point
                prev_point.next_point = tail_point
                prev_point = tail_point

            timeline.tail_point = tail_point

            timelines[timeline_id] = timeline
            timeline_children[parent_id, timeline.head_point.tick].append(timeline)
            self._next_new_timeline_id = max(self._next_new_timeline_id, timeline_id)

        # pass 2: add derived timelines to the appropriate points in each timeline.
        timeline_deque = deque()

        # root point is a special case, as it has no timeline associated with it
        for t in timeline_children[None, 0]:
            self.root_point.derivative_timelines.append(t)
            timeline_deque.append(t)

        del timeline_children[None, 0]

        while len(timeline_deque) > 0:
            cur_timeline = timeline_deque.popleft()
            cur_timeline_id = cur_timeline.timeline_id
            cur_point = cur_timeline.head_point

            while cur_point is not None:
                tick = cur_point.tick
                point_children_timelines = timeline_children.get((cur_timeline_id, tick), None)
                if point_children_timelines is not None:
                    cur_point.derivative_timelines.extend(point_children_timelines)
                    timeline_deque.extend(point_children_timelines)
                    del timeline_children[(cur_timeline_id, tick)]
                cur_point = cur_point.next_point

        if len(timeline_children) > 0:
            print(f"WARNING: Some timelines are not attached to the root point and have not been loaded.")
            print(timeline_children)

        self._timelines = timelines

    def get_timeline(self, timeline_id):
        return self._timelines.get(timeline_id, None)
