"""
@author: Matt Idzik (MidZik)
"""
from importlib import util
from multiprocessing.connection import Connection
from multiprocessing import Pipe, Process


class SimulationRunner:
    def __init__(self, simulation_folder_path):
        simulation_module_path = (simulation_folder_path / "simulation.pyd").resolve(True)
        spec = util.spec_from_file_location("simulation", simulation_module_path)
        self.module = util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

        self.simulation = self.module.Simulation()

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
            else:
                con.send((False, f"Unknown command '{cmd}'."))
        except EOFError:
            # connection closed, end the simulation
            break


class SimulationRunnerProcess:
    def __init__(self, simulation_folder_path):
        self._conn, child_conn = Pipe()
        self._process = Process(target=simulation_runner_loop, args=(child_conn, simulation_folder_path))

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

    def _send_command(self, command_str, *command_params):
        if not self._process.is_alive():
            raise RuntimeError("Unable to send command: process not running.")

        self._conn.send((command_str, command_params))
        success, result = self._conn.recv()
        if success:
            return result
        else:
            raise Exception(result)


class SimulationManager:
    def __init__(self):
        pass
