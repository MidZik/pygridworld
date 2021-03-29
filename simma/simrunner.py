"""
@author: Matt Idzik (MidZik)
"""
from subprocess import Popen, PIPE
from pathlib import Path

import grpc
import simulation_pb2 as sim
import simulation_pb2_grpc as sim_grpc

RpcError = grpc.RpcError


class SimulationProcess:
    _simulation_server_path = str(Path(__file__).parent /
                                  r'..\SimulationServer\bin\x64\Release\netcoreapp3.1\SimulationServer.exe')

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


class SimulationClient:
    @staticmethod
    def make_channel(address):
        return grpc.insecure_channel(address)

    def __init__(self, channel, token):
        self._channel = channel
        self.token = token

    def _create_metadata(self, *items):
        return (('x-user-token', self.token), *items)

    def start_simulation(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.StartSimulationRequest()
        stub.StartSimulation(request, metadata=self._create_metadata())

    def stop_simulation(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.StopSimulationRequest()
        stub.StopSimulation(request, metadata=self._create_metadata())

    def is_running(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.IsRunningRequest()
        response = stub.IsRunning(request, metadata=self._create_metadata())
        return response.running

    def get_tick(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetTickRequest()
        response = stub.GetTick(request, metadata=self._create_metadata())
        return response.tick

    def get_state_json(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetStateJsonRequest()
        response = stub.GetStateJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    def set_state_json(self, state_json: str):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetStateJsonRequest(json=state_json)
        stub.SetStateJson(request, metadata=self._create_metadata())

    def create_entity(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.CreateEntityRequest()
        response = stub.CreateEntity(request, metadata=self._create_metadata())
        return response.eid

    def destroy_entity(self, eid):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.DestroyEntityRequest(eid=eid)
        stub.DestroyEntity(request, metadata=self._create_metadata())

    def get_all_entities(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetAllEntitesRequest()
        response = stub.GetAllEntities(request, metadata=self._create_metadata())
        return response.eids, response.tick

    def assign_component(self, eid, com_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.AssignComponentRequest(eid=eid, component_name=com_name)
        stub.AssignComponent(request, metadata=self._create_metadata())

    def get_component_json(self, eid, com_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetComponentJsonRequest(eid=eid, component_name=com_name)
        response = stub.GetComponentJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    def remove_component(self, eid, com_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.RemoveComponentRequest(eid=eid, component_name=com_name)
        stub.RemoveComponent(request, metadata=self._create_metadata())

    def replace_component(self, eid, com_name, state_json):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.ReplaceComponentRequest(eid=eid, component_name=com_name, json=state_json)
        stub.ReplaceComponent(request, metadata=self._create_metadata())

    def get_component_names(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetComponentNamesRequest()
        response = stub.GetComponentNames(request, metadata=self._create_metadata())
        return response.component_names

    def get_entity_component_names(self, eid):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetEntityComponentNamesRequest(eid=eid)
        response = stub.GetEntityComponentNames(request, metadata=self._create_metadata())
        return response.component_names, response.tick

    def get_singleton_json(self, singleton_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetSingletonJsonRequest(singleton_name=singleton_name)
        response = stub.GetSingletonJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    def set_singleton_json(self, singleton_name, json):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetSingletonJsonRequest(singleton_name=singleton_name, json=json)
        stub.SetSingletonJson(request, metadata=self._create_metadata())

    def get_singleton_names(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetSingletonNamesRequest()
        response = stub.GetSingletonNames(request, metadata=self._create_metadata())
        return response.singleton_names

    class Event:
        def __init__(self, message):
            self.name = message.name

            if message.WhichOneof('data') == 'json':
                self.json = message.json
                self.bin = None
            else:
                self.json = None
                self.bin = message.bin

        def in_namespace(self, namespace: str):
            if not namespace[-1] == '.':
                namespace = namespace + '.'

            return self.name.startswith(namespace)

    class EventStreamContext:
        def __init__(self, responses):
            self.responses = responses

        def __iter__(self):
            return self

        def __next__(self):
            try:
                response = self.responses.__next__()
            except Exception as e:
                if e is self.responses:
                    # TEMP / TODO
                    # for now, assuming cancellation. Should maybe handle other cases.
                    raise StopIteration()
                raise
            return response.tick, [SimulationClient.Event(e) for e in response.events]

        def cancel(self):
            self.responses.cancel()

    def get_event_stream(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetEventsRequest()
        return self.EventStreamContext(stub.GetEvents(request, metadata=self._create_metadata()))

    def get_state_binary(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetStateBinaryRequest()
        response = stub.GetStateBinary(request, metadata=self._create_metadata())
        return response.binary, response.tick

    def set_state_binary(self, state_bin: bytes):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetStateBinaryRequest(binary=state_bin)
        stub.SetStateBinary(request, metadata=self._create_metadata())

    def run_command(self, args):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.RunCommandRequest(args=args)
        response = stub.RunCommand(request, metadata=self._create_metadata())
        return response.err, response.output

    def set_editor_token(self, token):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetEditorTokenRequest(token=token)
        stub.SetEditorToken(request, metadata=self._create_metadata())

    def is_editing(self, check_self_only=False):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.IsEditingRequest(check_self_only=check_self_only)
        response = stub.IsEditing(request, metadata=self._create_metadata())
        return response.is_editing
