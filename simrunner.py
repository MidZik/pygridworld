"""
@author: Matt Idzik (MidZik)
"""
from importlib import util
from multiprocessing.connection import Connection, wait
from multiprocessing import Pipe, Process
from threading import Lock, Thread
from pathlib import Path
import json
from datetime import datetime
import queue
import logging
import traceback


class SimulationRunner:
    """
    Loads and wraps the simulation module.
    """
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

    def get_all_entities(self):
        return self.simulation.get_all_entities()

    def assign_component(self, eid, com_name):
        self.simulation.assign_component(eid, com_name)

    def get_component_json(self, eid, com_name):
        return self.simulation.get_component_json(eid, com_name)

    def remove_component(self, eid, com_name):
        self.simulation.remove_component(eid, com_name)

    def replace_component(self, eid, com_name, state_json):
        self.simulation.replace_component(eid, com_name, state_json)

    def get_component_names(self):
        return self.simulation.get_component_names()

    def get_entity_component_names(self, eid):
        return self.simulation.get_entity_component_names(eid)

    def get_singleton_json(self, singleton_name):
        return self.simulation.get_singleton_json(singleton_name)

    def set_singleton_json(self, singleton_name, singleton_json):
        self.simulation.set_singleton_json(singleton_name, singleton_json)

    def get_singleton_names(self):
        return self.simulation.get_singleton_names()

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


def simulation_runner_loop(initial_con: Connection, simulation_folder_path, runner_working_dir, state_file_queue):
    def _on_state_file_written(tick, state_file_path):
        state_file_queue.put((tick, state_file_path))

    state_file_written_callback = _on_state_file_written if state_file_queue is not None else None

    runner = SimulationRunner(simulation_folder_path, runner_working_dir, state_file_written_callback)

    connections = [initial_con]
    halt_process = False

    try:
        while connections and not halt_process:
            ready_connections = wait(connections)
            for con in ready_connections:
                try:
                    cmd, params = con.recv()
                    if cmd == "stop_process":
                        con.send((True, None))
                        halt_process = True
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
                    elif cmd == "get_all_entities":
                        entities = runner.get_all_entities()
                        con.send((True, entities))
                    elif cmd == "assign_component":
                        eid, com_name = params
                        runner.assign_component(eid, com_name)
                        con.send((True, None))
                    elif cmd == "get_component_json":
                        eid, com_name = params
                        com_data = runner.get_component_json(eid, com_name)
                        con.send((True, com_data))
                    elif cmd == "remove_component":
                        eid, com_name = params
                        runner.remove_component(eid, com_name)
                        con.send((True, None))
                    elif cmd == "replace_component":
                        eid, com_name, state_json = params
                        runner.replace_component(eid, com_name, state_json)
                        con.send((True, None))
                    elif cmd == "get_component_names":
                        component_names = runner.get_component_names()
                        con.send((True, component_names))
                    elif cmd == "get_entity_component_names":
                        eid, = params
                        entity_component_names = runner.get_entity_component_names(eid)
                        con.send((True, entity_component_names))
                    elif cmd == "get_singleton_json":
                        singleton_name, = params
                        singleton_json = runner.get_singleton_json(singleton_name)
                        con.send((True, singleton_json))
                    elif cmd == "set_singleton_json":
                        singleton_name, singleton_json = params
                        runner.set_singleton_json(singleton_name, singleton_json)
                        con.send((True, None))
                    elif cmd == "get_singleton_names":
                        singleton_names = runner.get_singleton_names()
                        con.send((True, singleton_names))
                    elif cmd == "add_connection":
                        new_connection, = params
                        connections.append(new_connection)
                        con.send((True, None))
                    else:
                        con.send((False, f"Unknown command '{cmd}'."))
                except EOFError:
                    # connection closed
                    connections.remove(con)
                except Exception as e:
                    # for any non-exiting exception, write to stderr and continue listening for commands
                    # (this simulation may no longer function as expected, but that is up to the
                    # creator of this process to decide, not this function)
                    logging.error('SimulationRunner encountered a non-exiting exception.', exc_info=e)
                    con.send((False, traceback.format_exc()))
    finally:
        runner.cleanup()


class SimulationController:
    def __init__(self, connection):
        self._conn = connection

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj._lock = Lock()
        return obj

    def __getstate__(self):
        return self._conn

    def __setstate__(self, state):
        self._conn = state

    def stop_process(self):
        self._send_command("stop_process")

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

    def get_all_entities(self):
        return self._send_command("get_all_entities")

    def assign_component(self, eid, com_name):
        self._send_command("assign_component", eid, com_name)

    def get_component_json(self, eid, com_name):
        return self._send_command("get_component_json", eid, com_name)

    def remove_component(self, eid, com_name):
        self._send_command("remove_component", eid, com_name)

    def replace_component(self, eid, com_name, state_json):
        self._send_command("replace_component", eid, com_name, state_json)

    def get_component_names(self):
        return self._send_command("get_component_names")

    def get_entity_component_names(self, eid):
        return self._send_command("get_entity_component_names", eid)

    def get_singleton_json(self, singleton_name):
        return self._send_command("get_singleton_json", singleton_name)

    def set_singleton_json(self, singleton_name, singleton_json):
        self._send_command("set_singleton_json", singleton_name, singleton_json)

    def get_singleton_names(self):
        return self._send_command("get_singleton_names")

    def add_connection(self, new_connection: Connection):
        self._send_command("add_connection", new_connection)

    def new_controller(self):
        controller_con, sim_con = Pipe()
        self.add_connection(sim_con)
        return SimulationController(controller_con)

    def _send_command(self, command_str, *command_params):
        self._lock.acquire()
        self._conn.send((command_str, command_params))
        success, result = self._conn.recv()
        self._lock.release()
        if success:
            return result
        else:
            raise Exception(result)


class SimulationRunnerProcess:
    """
    Creates a SimulationRunner in a new process using multiprocessing.
    Responsible for communicating with the other process.
    """
    def __init__(self, simulation_folder_path, runner_working_dir, state_file_queue=None):
        controller_conn, child_conn = Pipe()
        args = (child_conn, simulation_folder_path, runner_working_dir, state_file_queue)
        self._process = Process(target=simulation_runner_loop, args=args, daemon=True)
        self.controller = SimulationController(controller_conn)

    def start_process(self):
        self._process.start()

    def join_process(self):
        self._process.join()
