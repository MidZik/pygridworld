import grpc
import simma.simulation_pb2 as sim
import simma.simulation_pb2_grpc as sim_grpc


RpcError = grpc.RpcError


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
        request = sim.GetAllEntitiesRequest()
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
