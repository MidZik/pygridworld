"""
@author: Matt Idzik (MidZik)
"""
from subprocess import Popen, PIPE
from threading import Thread
from typing import Optional
from pathlib import Path

import grpc
import simulation_pb2 as sim
import simulation_pb2_grpc as sim_grpc

RpcError = grpc.RpcError


class SimulationProcess:
    _simulation_server_path = str(Path(__file__).parent /
                                  r'.\SimulationServer\bin\x64\Release\netcoreapp3.1\SimulationServer.exe')

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

    def __init__(self, simulation_library_path, event_state_writer):
        self._simulation_library_path = simulation_library_path
        self._event_state_writer = event_state_writer

        self._process = None
        self._port = None
        self._client: Optional[SimulationClient] = None
        self._event_thread = None
        self._stream_context = None

    def __del__(self):
        self.stop()

    def start(self):
        process = Popen([SimulationProcess._simulation_server_path, 'serve', str(self._simulation_library_path)], stdout=PIPE, stdin=PIPE)
        self._process = process

        process.stdin.write(b"port\n")
        process.stdin.flush()
        self._port = int(process.stdout.readline())
        self._client = self.make_new_client()
        self._client.open()

        if self._event_state_writer:
            self._stream_context = self._client.get_event_stream()
            self._event_thread = Thread(target=self._event_handler)
            self._event_thread.start()

    def stop(self):
        if self._process.poll() is None:
            if self._event_state_writer:
                self._stream_context.cancel()
                self._event_thread.join()
            self._process.stdin.write(b"exit\n")
            self._process.stdin.flush()
            self._process.wait()

    def get_port(self):
        return self._port

    def get_server_address(self):
        return f'localhost:{self._port}'

    def get_client(self):
        return self._client

    def make_new_client(self):
        return SimulationClient(self.get_server_address())

    def _event_handler(self):
        for (tick, events) in self._stream_context:
            self._event_state_writer(tick, events)


class SimulationClient:
    def __init__(self, address):
        self._address = address
        self._channel = None

    def open(self):
        self._channel = grpc.insecure_channel(self._address)

    def close(self):
        self._channel.close()
        self._channel = None

    def start_simulation(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.StartSimulationRequest()
        stub.StartSimulation(request)

    def stop_simulation(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.StopSimulationRequest()
        stub.StopSimulation(request)

    def is_running(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.IsRunningRequest()
        response = stub.IsRunning(request)
        return response.running

    def get_tick(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetTickRequest()
        response = stub.GetTick(request)
        return response.tick

    def get_state_json(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetStateJsonRequest()
        response = stub.GetStateJson(request)
        return response.json

    def set_state_json(self, state_json: str):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetStateJsonRequest(json=state_json)
        stub.SetStateJson(request)

    def create_entity(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.CreateEntityRequest()
        response = stub.CreateEntity(request)
        return response.eid

    def destroy_entity(self, eid):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.DestroyEntityRequest(eid=eid)
        stub.DestroyEntity(request)

    def get_all_entities(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetAllEntitesRequest()
        response = stub.GetAllEntities(request)
        return response.eids

    def assign_component(self, eid, com_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.AssignComponentRequest(eid=eid, component_name=com_name)
        stub.AssignComponent(request)

    def get_component_json(self, eid, com_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetComponentJsonRequest(eid=eid, component_name=com_name)
        response = stub.GetComponentJson(request)
        return response.json

    def remove_component(self, eid, com_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.RemoveComponentRequest(eid=eid, component_name=com_name)
        stub.RemoveComponent(request)

    def replace_component(self, eid, com_name, state_json):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.ReplaceComponentRequest(eid=eid, component_name=com_name, json=state_json)
        stub.ReplaceComponent(request)

    def get_component_names(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetComponentNamesRequest()
        response = stub.GetComponentNames(request)
        return response.component_names

    def get_entity_component_names(self, eid):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetEntityComponentNamesRequest(eid=eid)
        response = stub.GetEntityComponentNames(request)
        return response.component_names

    def get_singleton_json(self, singleton_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetSingletonJsonRequest(singleton_name=singleton_name)
        response = stub.GetSingletonJson(request)
        return response.json

    def set_singleton_json(self, singleton_name, json):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetSingletonJsonRequest(singleton_name=singleton_name, json=json)
        stub.SetSingletonJson(request)

    def get_singleton_names(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetSingletonNamesRequest()
        response = stub.GetSingletonNames(request)
        return response.singleton_names

    class Event:
        def __init__(self, message):
            self.name = message.name

            if message.type == sim.EventMessage.Type.SIM:
                self.type = "SIM"
            elif message.type == sim.EventMessage.Type.META:
                self.type = "META"
            else:
                self.type = "UNKNOWN"

            if message.WhichOneof('data') == 'json':
                self.json = message.json
                self.data = None
            else:
                self.json = None
                self.data = message.data

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
                    # for now, assuming cancellation. Should maybe handle other cases.
                    raise StopIteration()
                raise
            return response.tick, [SimulationClient.Event(e) for e in response.events]

        def cancel(self):
            self.responses.cancel()

    def get_event_stream(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetEventsRequest()
        return self.EventStreamContext(stub.GetEvents(request))

    def get_state_binary(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetStateBinaryRequest()
        response = stub.GetStateBinary(request)
        return response.binary

    def set_state_binary(self, state_bin: str):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetStateBinaryRequest(binary=state_bin)
        stub.SetStateBinary(request)
