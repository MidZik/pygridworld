# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import simulation_pb2 as simulation__pb2


class SimulationStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.GetTick = channel.unary_unary(
        '/Simulation/GetTick',
        request_serializer=simulation__pb2.GetTickRequest.SerializeToString,
        response_deserializer=simulation__pb2.GetTickResponse.FromString,
        )
    self.GetStateJson = channel.unary_unary(
        '/Simulation/GetStateJson',
        request_serializer=simulation__pb2.GetStateJsonRequest.SerializeToString,
        response_deserializer=simulation__pb2.GetStateJsonResponse.FromString,
        )
    self.SetStateJson = channel.unary_unary(
        '/Simulation/SetStateJson',
        request_serializer=simulation__pb2.SetStateJsonRequest.SerializeToString,
        response_deserializer=simulation__pb2.SetStateJsonResponse.FromString,
        )
    self.CreateEntity = channel.unary_unary(
        '/Simulation/CreateEntity',
        request_serializer=simulation__pb2.CreateEntityRequest.SerializeToString,
        response_deserializer=simulation__pb2.CreateEntityResponse.FromString,
        )
    self.DestroyEntity = channel.unary_unary(
        '/Simulation/DestroyEntity',
        request_serializer=simulation__pb2.DestroyEntityRequest.SerializeToString,
        response_deserializer=simulation__pb2.DestroyEntityResponse.FromString,
        )
    self.GetAllEntities = channel.unary_unary(
        '/Simulation/GetAllEntities',
        request_serializer=simulation__pb2.GetAllEntitesRequest.SerializeToString,
        response_deserializer=simulation__pb2.GetAllEntitiesResponse.FromString,
        )
    self.StartSimulation = channel.unary_unary(
        '/Simulation/StartSimulation',
        request_serializer=simulation__pb2.StartSimulationRequest.SerializeToString,
        response_deserializer=simulation__pb2.StartSimulationResponse.FromString,
        )
    self.StopSimulation = channel.unary_unary(
        '/Simulation/StopSimulation',
        request_serializer=simulation__pb2.StopSimulationRequest.SerializeToString,
        response_deserializer=simulation__pb2.StopSimulationResponse.FromString,
        )
    self.IsRunning = channel.unary_unary(
        '/Simulation/IsRunning',
        request_serializer=simulation__pb2.IsRunningRequest.SerializeToString,
        response_deserializer=simulation__pb2.IsRunningResponse.FromString,
        )
    self.AssignComponent = channel.unary_unary(
        '/Simulation/AssignComponent',
        request_serializer=simulation__pb2.AssignComponentRequest.SerializeToString,
        response_deserializer=simulation__pb2.AssignComponentResponse.FromString,
        )
    self.GetComponentJson = channel.unary_unary(
        '/Simulation/GetComponentJson',
        request_serializer=simulation__pb2.GetComponentJsonRequest.SerializeToString,
        response_deserializer=simulation__pb2.GetComponentJsonResponse.FromString,
        )
    self.RemoveComponent = channel.unary_unary(
        '/Simulation/RemoveComponent',
        request_serializer=simulation__pb2.RemoveComponentRequest.SerializeToString,
        response_deserializer=simulation__pb2.RemoveComponentResponse.FromString,
        )
    self.ReplaceComponent = channel.unary_unary(
        '/Simulation/ReplaceComponent',
        request_serializer=simulation__pb2.ReplaceComponentRequest.SerializeToString,
        response_deserializer=simulation__pb2.ReplaceComponentResponse.FromString,
        )
    self.GetComponentNames = channel.unary_unary(
        '/Simulation/GetComponentNames',
        request_serializer=simulation__pb2.GetComponentNamesRequest.SerializeToString,
        response_deserializer=simulation__pb2.GetComponentNamesResponse.FromString,
        )
    self.GetEntityComponentNames = channel.unary_unary(
        '/Simulation/GetEntityComponentNames',
        request_serializer=simulation__pb2.GetEntityComponentNamesRequest.SerializeToString,
        response_deserializer=simulation__pb2.GetEntityComponentNamesResponse.FromString,
        )
    self.GetSingletonJson = channel.unary_unary(
        '/Simulation/GetSingletonJson',
        request_serializer=simulation__pb2.GetSingletonJsonRequest.SerializeToString,
        response_deserializer=simulation__pb2.GetSingletonJsonResponse.FromString,
        )
    self.SetSingletonJson = channel.unary_unary(
        '/Simulation/SetSingletonJson',
        request_serializer=simulation__pb2.SetSingletonJsonRequest.SerializeToString,
        response_deserializer=simulation__pb2.SetSingletonJsonResponse.FromString,
        )
    self.GetSingletonNames = channel.unary_unary(
        '/Simulation/GetSingletonNames',
        request_serializer=simulation__pb2.GetSingletonNamesRequest.SerializeToString,
        response_deserializer=simulation__pb2.GetSingletonNamesResponse.FromString,
        )
    self.GetEvents = channel.unary_stream(
        '/Simulation/GetEvents',
        request_serializer=simulation__pb2.GetEventsRequest.SerializeToString,
        response_deserializer=simulation__pb2.GetEventsResponse.FromString,
        )


class SimulationServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def GetTick(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetStateJson(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def SetStateJson(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def CreateEntity(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def DestroyEntity(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetAllEntities(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def StartSimulation(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def StopSimulation(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def IsRunning(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def AssignComponent(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetComponentJson(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def RemoveComponent(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def ReplaceComponent(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetComponentNames(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetEntityComponentNames(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetSingletonJson(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def SetSingletonJson(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetSingletonNames(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetEvents(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_SimulationServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'GetTick': grpc.unary_unary_rpc_method_handler(
          servicer.GetTick,
          request_deserializer=simulation__pb2.GetTickRequest.FromString,
          response_serializer=simulation__pb2.GetTickResponse.SerializeToString,
      ),
      'GetStateJson': grpc.unary_unary_rpc_method_handler(
          servicer.GetStateJson,
          request_deserializer=simulation__pb2.GetStateJsonRequest.FromString,
          response_serializer=simulation__pb2.GetStateJsonResponse.SerializeToString,
      ),
      'SetStateJson': grpc.unary_unary_rpc_method_handler(
          servicer.SetStateJson,
          request_deserializer=simulation__pb2.SetStateJsonRequest.FromString,
          response_serializer=simulation__pb2.SetStateJsonResponse.SerializeToString,
      ),
      'CreateEntity': grpc.unary_unary_rpc_method_handler(
          servicer.CreateEntity,
          request_deserializer=simulation__pb2.CreateEntityRequest.FromString,
          response_serializer=simulation__pb2.CreateEntityResponse.SerializeToString,
      ),
      'DestroyEntity': grpc.unary_unary_rpc_method_handler(
          servicer.DestroyEntity,
          request_deserializer=simulation__pb2.DestroyEntityRequest.FromString,
          response_serializer=simulation__pb2.DestroyEntityResponse.SerializeToString,
      ),
      'GetAllEntities': grpc.unary_unary_rpc_method_handler(
          servicer.GetAllEntities,
          request_deserializer=simulation__pb2.GetAllEntitesRequest.FromString,
          response_serializer=simulation__pb2.GetAllEntitiesResponse.SerializeToString,
      ),
      'StartSimulation': grpc.unary_unary_rpc_method_handler(
          servicer.StartSimulation,
          request_deserializer=simulation__pb2.StartSimulationRequest.FromString,
          response_serializer=simulation__pb2.StartSimulationResponse.SerializeToString,
      ),
      'StopSimulation': grpc.unary_unary_rpc_method_handler(
          servicer.StopSimulation,
          request_deserializer=simulation__pb2.StopSimulationRequest.FromString,
          response_serializer=simulation__pb2.StopSimulationResponse.SerializeToString,
      ),
      'IsRunning': grpc.unary_unary_rpc_method_handler(
          servicer.IsRunning,
          request_deserializer=simulation__pb2.IsRunningRequest.FromString,
          response_serializer=simulation__pb2.IsRunningResponse.SerializeToString,
      ),
      'AssignComponent': grpc.unary_unary_rpc_method_handler(
          servicer.AssignComponent,
          request_deserializer=simulation__pb2.AssignComponentRequest.FromString,
          response_serializer=simulation__pb2.AssignComponentResponse.SerializeToString,
      ),
      'GetComponentJson': grpc.unary_unary_rpc_method_handler(
          servicer.GetComponentJson,
          request_deserializer=simulation__pb2.GetComponentJsonRequest.FromString,
          response_serializer=simulation__pb2.GetComponentJsonResponse.SerializeToString,
      ),
      'RemoveComponent': grpc.unary_unary_rpc_method_handler(
          servicer.RemoveComponent,
          request_deserializer=simulation__pb2.RemoveComponentRequest.FromString,
          response_serializer=simulation__pb2.RemoveComponentResponse.SerializeToString,
      ),
      'ReplaceComponent': grpc.unary_unary_rpc_method_handler(
          servicer.ReplaceComponent,
          request_deserializer=simulation__pb2.ReplaceComponentRequest.FromString,
          response_serializer=simulation__pb2.ReplaceComponentResponse.SerializeToString,
      ),
      'GetComponentNames': grpc.unary_unary_rpc_method_handler(
          servicer.GetComponentNames,
          request_deserializer=simulation__pb2.GetComponentNamesRequest.FromString,
          response_serializer=simulation__pb2.GetComponentNamesResponse.SerializeToString,
      ),
      'GetEntityComponentNames': grpc.unary_unary_rpc_method_handler(
          servicer.GetEntityComponentNames,
          request_deserializer=simulation__pb2.GetEntityComponentNamesRequest.FromString,
          response_serializer=simulation__pb2.GetEntityComponentNamesResponse.SerializeToString,
      ),
      'GetSingletonJson': grpc.unary_unary_rpc_method_handler(
          servicer.GetSingletonJson,
          request_deserializer=simulation__pb2.GetSingletonJsonRequest.FromString,
          response_serializer=simulation__pb2.GetSingletonJsonResponse.SerializeToString,
      ),
      'SetSingletonJson': grpc.unary_unary_rpc_method_handler(
          servicer.SetSingletonJson,
          request_deserializer=simulation__pb2.SetSingletonJsonRequest.FromString,
          response_serializer=simulation__pb2.SetSingletonJsonResponse.SerializeToString,
      ),
      'GetSingletonNames': grpc.unary_unary_rpc_method_handler(
          servicer.GetSingletonNames,
          request_deserializer=simulation__pb2.GetSingletonNamesRequest.FromString,
          response_serializer=simulation__pb2.GetSingletonNamesResponse.SerializeToString,
      ),
      'GetEvents': grpc.unary_stream_rpc_method_handler(
          servicer.GetEvents,
          request_deserializer=simulation__pb2.GetEventsRequest.FromString,
          response_serializer=simulation__pb2.GetEventsResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'Simulation', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
