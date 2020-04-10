"""
@author: Matt Idzik (MidZik)
"""
from importlib import util
from multiprocessing.connection import Connection
from multiprocessing import Pipe, Process
from threading import Lock
import json


class SimulationRunner:
    def __init__(self, simulation_folder_path):
        simulation_module_path = (simulation_folder_path / "simulation.pyd").resolve(True)
        spec = util.spec_from_file_location("simulation", simulation_module_path)
        self.module = util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

        self.simulation = self.module.Simulation()
        self.simulation.set_event_callback(self._on_simulation_event)

    def start_simulation(self):
        self.simulation.start_simulation()

    def stop_simulation(self):
        self.simulation.stop_simulation()

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
        state_json = self.get_state_json()
        state_obj = json.loads(state_json)


def simulation_runner_loop(con: Connection, simulation_folder_path):
    runner = SimulationRunner(simulation_folder_path)

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


class SimulationRunnerProcess:
    def __init__(self, simulation_folder_path):
        self._conn, child_conn = Pipe()
        self._process = Process(target=simulation_runner_loop, args=(child_conn, simulation_folder_path), daemon=True)
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


class SimulationManager:
    def __init__(self):
        pass
