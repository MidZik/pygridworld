﻿using Grpc.Core;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SimulationServer
{
    class SimulationService : Simulation.SimulationBase
    {
        private SimulationWrapper simulation;
        private event SimulationWrapper.StringResultHandler simulation_event;

        public SimulationService(SimulationWrapper p_simulation)
        {
            simulation = p_simulation;
            simulation.SetEventCallback(EventCallback);
        }

        private void EventCallback(string s)
        {
            simulation_event(s);
        }

        public override Task<AssignComponentResponse> AssignComponent(AssignComponentRequest request, ServerCallContext context)
        {
            simulation.AssignComponent(request.Eid, request.ComponentName);
            return Task.FromResult(new AssignComponentResponse { });
        }

        public override Task<CreateEntityResponse> CreateEntity(CreateEntityRequest request, ServerCallContext context)
        {
            ulong eid = simulation.CreateEntity();
            return Task.FromResult(new CreateEntityResponse { Eid = eid });
        }

        public override Task<DestroyEntityResponse> DestroyEntity(DestroyEntityRequest request, ServerCallContext context)
        {
            simulation.DestroyEntity(request.Eid);
            return Task.FromResult(new DestroyEntityResponse { });
        }

        public override Task<GetAllEntitiesResponse> GetAllEntities(GetAllEntitesRequest request, ServerCallContext context)
        {
            List<ulong> eids = simulation.GetAllEntities();
            GetAllEntitiesResponse result = new GetAllEntitiesResponse();
            result.Eids.Add(eids);
            return Task.FromResult(result);
        }

        public override Task<GetComponentJsonResponse> GetComponentJson(GetComponentJsonRequest request, ServerCallContext context)
        {
            string json = simulation.GetComponentJson(request.Eid, request.ComponentName);
            return Task.FromResult(new GetComponentJsonResponse { Json = json });
        }

        public override Task<GetComponentNamesResponse> GetComponentNames(GetComponentNamesRequest request, ServerCallContext context)
        {
            List<string> names = simulation.GetComponentNames();
            GetComponentNamesResponse result = new GetComponentNamesResponse();
            result.ComponentNames.Add(names);
            return Task.FromResult(result);
        }

        public override Task<GetEntityComponentNamesResponse> GetEntityComponentNames(GetEntityComponentNamesRequest request, ServerCallContext context)
        {
            List<string> names = simulation.GetEntityComponentNames(request.Eid);
            GetEntityComponentNamesResponse result = new GetEntityComponentNamesResponse();
            result.ComponentNames.Add(names);
            return Task.FromResult(result);
        }

        public override async Task GetEvents(GetEventsRequest request, IServerStreamWriter<GetEventsResponse> responseStream, ServerCallContext context)
        {
            SimulationWrapper.StringResultHandler handler = async (string s) =>
            {
                await responseStream.WriteAsync(new GetEventsResponse { Data = s });
            };
            simulation_event += handler;
            context.CancellationToken.Register(() => simulation_event -= handler);
        }

        public override Task<GetSingletonJsonResponse> GetSingletonJson(GetSingletonJsonRequest request, ServerCallContext context)
        {
            string json = simulation.GetSingletonJson(request.SingletonName);
            return Task.FromResult(new GetSingletonJsonResponse { Json = json });
        }

        public override Task<GetSingletonNamesResponse> GetSingletonNames(GetSingletonNamesRequest request, ServerCallContext context)
        {
            List<string> names = simulation.GetSingletonNames();
            GetSingletonNamesResponse result = new GetSingletonNamesResponse();
            result.SingletonNames.Add(names);
            return Task.FromResult(result);
        }

        public override Task<GetStateJsonResponse> GetStateJson(GetStateJsonRequest request, ServerCallContext context)
        {
            string json = simulation.GetStateJson();
            return Task.FromResult(new GetStateJsonResponse { Json = json });
        }

        public override Task<GetTickResponse> GetTick(GetTickRequest request, ServerCallContext context)
        {
            ulong tick = simulation.GetTick();
            return Task.FromResult(new GetTickResponse { Tick = tick });
        }

        public override Task<IsRunningResponse> IsRunning(IsRunningRequest request, ServerCallContext context)
        {
            bool is_running = simulation.IsRunning();
            return Task.FromResult(new IsRunningResponse { Running = is_running });
        }

        public override Task<RemoveComponentResponse> RemoveComponent(RemoveComponentRequest request, ServerCallContext context)
        {
            simulation.RemoveComponent(request.Eid, request.ComponentName);
            return Task.FromResult(new RemoveComponentResponse { });
        }

        public override Task<ReplaceComponentResponse> ReplaceComponent(ReplaceComponentRequest request, ServerCallContext context)
        {
            simulation.ReplaceComponent(request.Eid, request.ComponentName, request.Json);
            return Task.FromResult(new ReplaceComponentResponse { });
        }

        public override Task<SetSingletonJsonResponse> SetSingletonJson(SetSingletonJsonRequest request, ServerCallContext context)
        {
            simulation.SetSingletonJson(request.SingletonName, request.Json);
            return Task.FromResult(new SetSingletonJsonResponse { });
        }

        public override Task<SetStateJsonResponse> SetStateJson(SetStateJsonRequest request, ServerCallContext context)
        {
            simulation.SetStateJson(request.Json);
            return Task.FromResult(new SetStateJsonResponse { });
        }

        public override Task<StartSimulationResponse> StartSimulation(StartSimulationRequest request, ServerCallContext context)
        {
            simulation.StartSimulation();
            return Task.FromResult(new StartSimulationResponse { });
        }

        public override Task<StopSimulationResponse> StopSimulation(StopSimulationRequest request, ServerCallContext context)
        {
            simulation.StopSimulation();
            return Task.FromResult(new StopSimulationResponse { });
        }
    }

}
