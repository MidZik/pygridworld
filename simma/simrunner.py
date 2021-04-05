"""
@author: Matt Idzik (MidZik)
"""
from subprocess import Popen, PIPE
from pathlib import Path

from simma.sim_client import SimulationClient


class SimulationProcess:
    _simulation_server_path = str(Path(__file__).parent / r'lib/SimulationServer.exe')

    @staticmethod
    def simple_convert(input_file: str,
                       input_format: str,
                       input_sim_path: str,
                       output_file: str,
                       output_format: str,
                       output_sim_path: str = None):
        args = []
        args.append(SimulationProcess._simulation_server_path)
        args.append('convert')
        args.extend(('-i', input_file))
        args.extend(('-if', input_format))
        args.extend(('-is', input_sim_path))
        args.extend(('-o', output_file))
        args.extend(('-of', output_format))
        if output_sim_path:
            args.extend(('-os', output_sim_path))
        process = Popen(args)
        result = process.wait()
        if result != 0:
            raise RuntimeError("File conversion failed.")

    @staticmethod
    def convert_multiple(input_files,
                         input_format: str,
                         input_sim_path: str,
                         output_files,
                         output_format: str,
                         output_sim_path: str = None):
        args = []
        args.append(SimulationProcess._simulation_server_path)
        args.append('convert')
        args.extend(('-if', input_format))
        args.extend(('-is', input_sim_path))
        args.extend(('-of', output_format))
        args.append('-iofi')
        if output_sim_path:
            args.extend(('-os', output_sim_path))
        process = Popen(args, stdin=PIPE, text=True)
        for i, o in zip(input_files, output_files):
            process.stdin.write(i + "\n")
            process.stdin.write(o + "\n")
            process.stdin.flush()
        process.stdin.write("\n")
        process.stdin.flush()
        result = process.wait()
        if result != 0:
            raise RuntimeError("File conversions failed.")

    @staticmethod
    def convert_multiple_generator(input_format: str,
                                   input_sim_path: str,
                                   output_format: str,
                                   output_sim_path: str = None):
        args = []
        args.append(SimulationProcess._simulation_server_path)
        args.append('convert')
        args.extend(('-if', input_format))
        args.extend(('-is', input_sim_path))
        args.extend(('-of', output_format))
        args.append('-iofi')
        if output_sim_path:
            args.extend(('-os', output_sim_path))
        process = Popen(args, stdin=PIPE, stdout=PIPE, text=True)
        input_file = yield
        while input_file:
            process.stdin.write(input_file + "\n")
            process.stdin.write("\n")
            process.stdin.flush()
            output = process.stdout.readline()
            input_file = yield output
        process.stdin.write("\n")
        process.stdin.flush()
        result = process.wait()
        if result != 0:
            raise RuntimeError("File conversions failed.")

    @staticmethod
    def create_default(output_file: str,
                       output_format: str,
                       output_sim_path: str):
        args = []
        args.append(SimulationProcess._simulation_server_path)
        args.append('create-default')
        args.extend(('-o', output_file))
        args.extend(('-of', output_format))
        args.extend(('-os', output_sim_path))
        process = Popen(args)
        result = process.wait()
        if result != 0:
            raise RuntimeError("Creating default state file failed.")

    def __init__(self, simulation_library_path):
        self._simulation_library_path = simulation_library_path

        self._process = None
        self._port = None
        self._channel = None

    def __del__(self):
        self.stop()

    def start(self, owner_token=""):
        process = Popen([
            SimulationProcess._simulation_server_path,
            'serve',
            '-o', owner_token,
            str(self._simulation_library_path)],
                        stdout=PIPE, stdin=PIPE)
        self._process = process

        process.stdin.write(b"port\n")
        process.stdin.flush()
        self._port = int(process.stdout.readline())

        self._channel = SimulationClient.make_channel(self.get_server_address())

    def stop(self):
        if self._process.poll() is None:
            self._channel.close()
            self._channel = None
            self._process.stdin.write(b"exit\n")
            self._process.stdin.flush()
            self._process.wait()

    def get_port(self):
        return self._port

    def get_server_address(self):
        return f'localhost:{self._port}'

    def make_client(self, token=""):
        return SimulationClient(self._channel, token)
