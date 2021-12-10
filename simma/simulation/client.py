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
    def make_channel(address):
        return grpc.aio.insecure_channel(address)

    def __init__(self, channel, token):
        self._channel = channel
        self.token = token
        self._stub = sim_grpc.SimulationStub(self._channel)

    def _create_metadata(self, *items):
        return ('x-user-token', self.token), *items

    async def start_simulation(self):
        request = sim.StartSimulationRequest()
        await self._stub.StartSimulation(request, metadata=self._create_metadata())

    async def stop_simulation(self):
        request = sim.StopSimulationRequest()
        await self._stub.StopSimulation(request, metadata=self._create_metadata())

    async def is_running(self):
        request = sim.IsRunningRequest()
        response = await self._stub.IsRunning(request, metadata=self._create_metadata())
        return response.running

    async def get_tick(self):
        request = sim.GetTickRequest()
        response = await self._stub.GetTick(request, metadata=self._create_metadata())
        return response.tick

    async def get_state_json(self):
        request = sim.GetStateJsonRequest()
        response = await self._stub.GetStateJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    async def set_state_json(self, state_json: str):
        request = sim.SetStateJsonRequest(json=state_json)
        await self._stub.SetStateJson(request, metadata=self._create_metadata())

    async def create_entity(self):
        request = sim.CreateEntityRequest()
        response = await self._stub.CreateEntity(request, metadata=self._create_metadata())
        return response.eid

    async def destroy_entity(self, eid):
        request = sim.DestroyEntityRequest(eid=eid)
        await self._stub.DestroyEntity(request, metadata=self._create_metadata())

    async def get_all_entities(self):
        request = sim.GetAllEntitiesRequest()
        response = await self._stub.GetAllEntities(request, metadata=self._create_metadata())
        return response.eids, response.tick

    async def assign_component(self, eid, com_name):
        request = sim.AssignComponentRequest(eid=eid, component_name=com_name)
        await self._stub.AssignComponent(request, metadata=self._create_metadata())

    async def get_component_json(self, eid, com_name):
        request = sim.GetComponentJsonRequest(eid=eid, component_name=com_name)
        response = await self._stub.GetComponentJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    async def remove_component(self, eid, com_name):
        request = sim.RemoveComponentRequest(eid=eid, component_name=com_name)
        await self._stub.RemoveComponent(request, metadata=self._create_metadata())

    async def replace_component(self, eid, com_name, state_json):
        request = sim.ReplaceComponentRequest(eid=eid, component_name=com_name, json=state_json)
        await self._stub.ReplaceComponent(request, metadata=self._create_metadata())

    async def get_component_names(self):
        request = sim.GetComponentNamesRequest()
        response = await self._stub.GetComponentNames(request, metadata=self._create_metadata())
        return response.component_names

    async def get_entity_component_names(self, eid):
        request = sim.GetEntityComponentNamesRequest(eid=eid)
        response = await self._stub.GetEntityComponentNames(request, metadata=self._create_metadata())
        return response.component_names, response.tick

    async def get_singleton_json(self, singleton_name):
        request = sim.GetSingletonJsonRequest(singleton_name=singleton_name)
        response = await self._stub.GetSingletonJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    async def set_singleton_json(self, singleton_name, json):
        request = sim.SetSingletonJsonRequest(singleton_name=singleton_name, json=json)
        await self._stub.SetSingletonJson(request, metadata=self._create_metadata())

    async def get_singleton_names(self):
        request = sim.GetSingletonNamesRequest()
        response = await self._stub.GetSingletonNames(request, metadata=self._create_metadata())
        return response.singleton_names

    async def get_event_stream(self):
        request = sim.GetEventsRequest()
        async for response in self._stub.GetEvents(request, metadata=self._create_metadata()):
            yield response.tick, [Event(e) for e in response.events]

    async def get_state_binary(self):
        request = sim.GetStateBinaryRequest()
        response = await self._stub.GetStateBinary(request, metadata=self._create_metadata())
        return response.binary, response.tick

    async def set_state_binary(self, state_bin: bytes):
        request = sim.SetStateBinaryRequest(binary=state_bin)
        await self._stub.SetStateBinary(request, metadata=self._create_metadata())

    async def run_command(self, args):
        request = sim.RunCommandRequest(args=args)
        response = await self._stub.RunCommand(request, metadata=self._create_metadata())
        return response.err, response.output

    async def set_editor_token(self, token):
        request = sim.SetEditorTokenRequest(token=token)
        await self._stub.SetEditorToken(request, metadata=self._create_metadata())

    async def is_editing(self, check_self_only=False):
        request = sim.IsEditingRequest(check_self_only=check_self_only)
        response = await self._stub.IsEditing(request, metadata=self._create_metadata())
        return response.is_editing


class SyncClient:
    @staticmethod
    def make_channel(address):
        return grpc.insecure_channel(address)

    def __init__(self, channel, token):
        self._channel = channel
        self.token = token
        self._stub = sim_grpc.SimulationStub(self._channel)

    def _create_metadata(self, *items):
        return ('x-user-token', self.token), *items

    def start_simulation(self):
        request = sim.StartSimulationRequest()
        self._stub.StartSimulation(request, metadata=self._create_metadata())

    def stop_simulation(self):
        request = sim.StopSimulationRequest()
        self._stub.StopSimulation(request, metadata=self._create_metadata())

    def is_running(self):
        request = sim.IsRunningRequest()
        response = self._stub.IsRunning(request, metadata=self._create_metadata())
        return response.running

    def get_tick(self):
        request = sim.GetTickRequest()
        response = self._stub.GetTick(request, metadata=self._create_metadata())
        return response.tick

    def get_state_json(self):
        request = sim.GetStateJsonRequest()
        response = self._stub.GetStateJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    def set_state_json(self, state_json: str):
        request = sim.SetStateJsonRequest(json=state_json)
        self._stub.SetStateJson(request, metadata=self._create_metadata())

    def create_entity(self):
        request = sim.CreateEntityRequest()
        response = self._stub.CreateEntity(request, metadata=self._create_metadata())
        return response.eid

    def destroy_entity(self, eid):
        request = sim.DestroyEntityRequest(eid=eid)
        self._stub.DestroyEntity(request, metadata=self._create_metadata())

    def get_all_entities(self):
        request = sim.GetAllEntitiesRequest()
        response = self._stub.GetAllEntities(request, metadata=self._create_metadata())
        return response.eids, response.tick

    def assign_component(self, eid, com_name):
        request = sim.AssignComponentRequest(eid=eid, component_name=com_name)
        self._stub.AssignComponent(request, metadata=self._create_metadata())

    def get_component_json(self, eid, com_name):
        request = sim.GetComponentJsonRequest(eid=eid, component_name=com_name)
        response = self._stub.GetComponentJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    def remove_component(self, eid, com_name):
        request = sim.RemoveComponentRequest(eid=eid, component_name=com_name)
        self._stub.RemoveComponent(request, metadata=self._create_metadata())

    def replace_component(self, eid, com_name, state_json):
        request = sim.ReplaceComponentRequest(eid=eid, component_name=com_name, json=state_json)
        self._stub.ReplaceComponent(request, metadata=self._create_metadata())

    def get_component_names(self):
        request = sim.GetComponentNamesRequest()
        response = self._stub.GetComponentNames(request, metadata=self._create_metadata())
        return response.component_names

    def get_entity_component_names(self, eid):
        request = sim.GetEntityComponentNamesRequest(eid=eid)
        response = self._stub.GetEntityComponentNames(request, metadata=self._create_metadata())
        return response.component_names, response.tick

    def get_singleton_json(self, singleton_name):
        request = sim.GetSingletonJsonRequest(singleton_name=singleton_name)
        response = self._stub.GetSingletonJson(request, metadata=self._create_metadata())
        return response.json, response.tick

    def set_singleton_json(self, singleton_name, json):
        request = sim.SetSingletonJsonRequest(singleton_name=singleton_name, json=json)
        self._stub.SetSingletonJson(request, metadata=self._create_metadata())

    def get_singleton_names(self):
        request = sim.GetSingletonNamesRequest()
        response = self._stub.GetSingletonNames(request, metadata=self._create_metadata())
        return response.singleton_names

    def get_event_stream(self):
        request = sim.GetEventsRequest()
        for response in self._stub.GetEvents(request, metadata=self._create_metadata()):
            yield response.tick, [Event(e) for e in response.events]

    def get_state_binary(self):
        request = sim.GetStateBinaryRequest()
        response = self._stub.GetStateBinary(request, metadata=self._create_metadata())
        return response.binary, response.tick

    def set_state_binary(self, state_bin: bytes):
        request = sim.SetStateBinaryRequest(binary=state_bin)
        self._stub.SetStateBinary(request, metadata=self._create_metadata())

    def run_command(self, args):
        request = sim.RunCommandRequest(args=args)
        response = self._stub.RunCommand(request, metadata=self._create_metadata())
        return response.err, response.output

    def set_editor_token(self, token):
        request = sim.SetEditorTokenRequest(token=token)
        self._stub.SetEditorToken(request, metadata=self._create_metadata())

    def is_editing(self, check_self_only=False):
        request = sim.IsEditingRequest(check_self_only=check_self_only)
        response = self._stub.IsEditing(request, metadata=self._create_metadata())
        return response.is_editing
