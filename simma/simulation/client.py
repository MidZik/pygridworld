import grpc
import simma.simulation_pb2 as sim
import simma.simulation_pb2_grpc as sim_grpc

# TODO: based on sim_client, remove sim_client when this file is finalized


RpcError = grpc.RpcError


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


class Client:
    @staticmethod
    async def make_channel(address):
        return await grpc.aio.insecure_channel(address)

    def __init__(self, channel, token):
        self._channel = channel
        self.token = token

    def _create_metadata(self, *items):
        return ('x-user-token', self.token), *items

    async def start_simulation(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.StartSimulationRequest()
        await stub.StartSimulation(request, metadata=self._create_metadata())

    async def stop_simulation(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.StopSimulationRequest()
        await stub.StopSimulation(request, metadata=self._create_metadata())

    async def is_running(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.IsRunningRequest()
        response = await stub.IsRunning(request, metadata=self._create_metadata())
        return response.running

    async def get_tick(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetTickRequest()
        response = await stub.GetTick(request, metadata=self._create_metadata())
        return response.tick

    async def get_state_json(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetStateJsonRequest()
        response = await stub.GetStateJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    async def set_state_json(self, state_json: str):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetStateJsonRequest(json=state_json)
        await stub.SetStateJson(request, metadata=self._create_metadata())

    async def create_entity(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.CreateEntityRequest()
        response = await stub.CreateEntity(request, metadata=self._create_metadata())
        return response.eid

    async def destroy_entity(self, eid):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.DestroyEntityRequest(eid=eid)
        await stub.DestroyEntity(request, metadata=self._create_metadata())

    async def get_all_entities(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetAllEntitiesRequest()
        response = await stub.GetAllEntities(request, metadata=self._create_metadata())
        return response.eids, response.tick

    async def assign_component(self, eid, com_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.AssignComponentRequest(eid=eid, component_name=com_name)
        await stub.AssignComponent(request, metadata=self._create_metadata())

    async def get_component_json(self, eid, com_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetComponentJsonRequest(eid=eid, component_name=com_name)
        response = await stub.GetComponentJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    async def remove_component(self, eid, com_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.RemoveComponentRequest(eid=eid, component_name=com_name)
        await stub.RemoveComponent(request, metadata=self._create_metadata())

    async def replace_component(self, eid, com_name, state_json):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.ReplaceComponentRequest(eid=eid, component_name=com_name, json=state_json)
        await stub.ReplaceComponent(request, metadata=self._create_metadata())

    async def get_component_names(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetComponentNamesRequest()
        response = await stub.GetComponentNames(request, metadata=self._create_metadata())
        return response.component_names

    async def get_entity_component_names(self, eid):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetEntityComponentNamesRequest(eid=eid)
        response = await stub.GetEntityComponentNames(request, metadata=self._create_metadata())
        return response.component_names, response.tick

    async def get_singleton_json(self, singleton_name):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetSingletonJsonRequest(singleton_name=singleton_name)
        response = await stub.GetSingletonJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    async def set_singleton_json(self, singleton_name, json):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetSingletonJsonRequest(singleton_name=singleton_name, json=json)
        await stub.SetSingletonJson(request, metadata=self._create_metadata())

    async def get_singleton_names(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetSingletonNamesRequest()
        response = await stub.GetSingletonNames(request, metadata=self._create_metadata())
        return response.singleton_names

    async def get_event_stream(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetEventsRequest()
        async for response in stub.GetEvents(request, metadata=self._create_metadata()):
            yield response.tick, [Event(e) for e in response.events]

    async def get_state_binary(self):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.GetStateBinaryRequest()
        response = await stub.GetStateBinary(request, metadata=self._create_metadata())
        return response.binary, response.tick

    async def set_state_binary(self, state_bin: bytes):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetStateBinaryRequest(binary=state_bin)
        await stub.SetStateBinary(request, metadata=self._create_metadata())

    async def run_command(self, args):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.RunCommandRequest(args=args)
        response = await stub.RunCommand(request, metadata=self._create_metadata())
        return response.err, response.output

    async def set_editor_token(self, token):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.SetEditorTokenRequest(token=token)
        await stub.SetEditorToken(request, metadata=self._create_metadata())

    async def is_editing(self, check_self_only=False):
        stub = sim_grpc.SimulationStub(self._channel)
        request = sim.IsEditingRequest(check_self_only=check_self_only)
        response = await stub.IsEditing(request, metadata=self._create_metadata())
        return response.is_editing
