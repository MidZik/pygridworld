using Grpc.Core;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using PyGridWorld.SimulationServer;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Collections.Concurrent;
using System.Threading.Tasks.Dataflow;


namespace SimulationServer
{
    class SimulationService : Simulation.SimulationBase
    {
        [Flags]
        private enum TickEventFlags
        {
            None = 0,
            EventsOccurred = 1,
        }

        private struct EventsData
        {
            public ulong tick;
            public List<EventMessage> events;
        }

        private SimulationWrapper simulation;
        private delegate void CommitEventsDelegate(EventsData data);
        private event CommitEventsDelegate events_committed;
        private System.Diagnostics.Stopwatch performanceStopwatch = new System.Diagnostics.Stopwatch();
        private ulong performanceStartTick = 0, performanceStopTick = 0;
        private ulong stopAtTick = 0;

        public SimulationService(SimulationWrapper simulation)
        {
            this.simulation = simulation;
            simulation.SetTickEventCallback(TickEventCallback);
        }

        private void TickEventCallback(ulong tick, ulong raw_flags)
        {
            List<EventMessage> event_messages = new List<EventMessage>();
            TickEventFlags flags = (TickEventFlags)raw_flags;
            if (flags.HasFlag(TickEventFlags.EventsOccurred))
            {
                SimulationWrapper.SimEventHandler sim_event_handler = (string name, string json) =>
                {
                    event_messages.Add(new EventMessage()
                    {
                        Name = "sim." + name,
                        Json = json
                    });
                };

                simulation.GetEventsLastTick(sim_event_handler);
            }

            // TEMP/TODO: this value will be configurable
            if (tick % 500000 == 0)
            {
                byte[] state_binary = simulation.GetStateBinary();
                event_messages.Add(new EventMessage()
                {
                    Name = "meta.state_bin",
                    Bin = Google.Protobuf.ByteString.CopyFrom(state_binary)
                });
            }

            if (event_messages.Count > 0)
            {
                events_committed(new EventsData { tick = tick, events = event_messages });
            }

            if (stopAtTick > 0 && tick >= stopAtTick)
            {
                simulation.RequestStop();
                Task.Factory.StartNew(StopSimulationImpl);
            }
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
            var eventsDataQueue = new BufferBlock<EventsData>(new DataflowBlockOptions
            {
                CancellationToken = context.CancellationToken,
                EnsureOrdered = true,
                BoundedCapacity = 100
            });

            CommitEventsDelegate addToQueueHandler = (EventsData data) =>
            {
                eventsDataQueue.SendAsync(data).Wait();
            };

            events_committed += addToQueueHandler;

            while (!context.CancellationToken.IsCancellationRequested)
            {
                EventsData data = await eventsDataQueue.ReceiveAsync(context.CancellationToken);
                GetEventsResponse response = new GetEventsResponse();
                response.Tick = data.tick;
                response.Events.AddRange(data.events);
                await responseStream.WriteAsync(response);
            }

            events_committed -= addToQueueHandler;
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
            StartSimulationImpl();
            return Task.FromResult(new StartSimulationResponse { });
        }

        public override Task<StopSimulationResponse> StopSimulation(StopSimulationRequest request, ServerCallContext context)
        {
            StopSimulationImpl();
            return Task.FromResult(new StopSimulationResponse { });
        }

        public override Task<GetStateBinaryResponse> GetStateBinary(GetStateBinaryRequest request, ServerCallContext context)
        {
            byte[] bin = simulation.GetStateBinary();
            return Task.FromResult(new GetStateBinaryResponse { Binary = Google.Protobuf.ByteString.CopyFrom(bin) });
        }

        public override Task<SetStateBinaryResponse> SetStateBinary(SetStateBinaryRequest request, ServerCallContext context)
        {
            simulation.SetStateBinary(request.Binary.ToByteArray());
            return Task.FromResult(new SetStateBinaryResponse { });
        }

        public override Task<RunCommandResponse> RunCommand(RunCommandRequest request, ServerCallContext context)
        {
            string err = null;
            string output = null;

            var args = request.Args;

            if (args.Count == 0)
            {
                err = "No command provided.";
            }
            else
            {
                switch (args[0])
                {
                    case "sim":
                        {
                            // "sim ..."
                            (err, output) = simulation.RunCommand(args.Skip(1).ToArray());
                            break;
                        }
                    case "run":
                        {
                            StartSimulationImpl();
                            break;
                        }
                    case "run_until":
                        {
                            try
                            {
                                ulong until_tick = ulong.Parse(args[1], System.Globalization.CultureInfo.InvariantCulture);
                                StartSimulationImpl(until_tick);
                            }
                            catch
                            {
                                err = "'run_until <tick>' format was incorrect";
                            }
                            break;
                        }
                    case "run_for":
                        {
                            ulong for_tick_count;

                            try
                            {
                                for_tick_count = ulong.Parse(args[1], System.Globalization.CultureInfo.InvariantCulture);
                            }
                            catch
                            {
                                err = "'run for <tick_count>' format was incorrect";
                                break;
                            }

                            ulong until_tick = simulation.GetTick() + for_tick_count;
                            StartSimulationImpl(until_tick);
                            break;
                        }
                    case "perf":
                        {
                            if (simulation.IsRunning())
                            {
                                err = "'perf' can only be used while the simulation isn't running.";
                            }
                            else if (performanceStartTick == performanceStopTick)
                            {
                                err = "'perf' requires that the simulation runs for at least one tick.";
                            }
                            else
                            {
                                ulong ticks = performanceStopTick - performanceStartTick;
                                double timeInSec = performanceStopwatch.Elapsed.TotalSeconds;
                                double timePerKilotick = (timeInSec * 1000 / ticks);
                                double kiloticksPerSec = (ticks / timeInSec / 1000);
                                output = $"Ticks: {ticks}\nTime(sec): {timeInSec}\nTime Per Kilotick: {timePerKilotick}\nKiloticks Per Second: {kiloticksPerSec}";
                            }
                            break;
                        }
                    case "tick":
                        {
                            output = simulation.GetTick().ToString();
                            break;
                        }
                    default:
                        {
                            err = $"Unknown command '{args[0]}'";
                            break;
                        }
                }
            }

            return Task.FromResult(new RunCommandResponse { Err = err ?? string.Empty, Output = output ?? string.Empty });

        }

        private void SendRunnerUpdateEvent(ulong tick, bool sim_running)
        {
            List<EventMessage> event_messages = new List<EventMessage>();

            event_messages.Add(new EventMessage
            {
                Name = "runner.update",
                Json = JsonSerializer.Serialize(new
                {
                    sim_running = sim_running,
                })
            });

            events_committed(new EventsData { tick = tick, events = event_messages });
        }

        private void StartSimulationImpl(ulong p_stopAtTick = 0)
        {
            stopAtTick = p_stopAtTick;
            if (!simulation.IsRunning() && (stopAtTick == 0 || simulation.GetTick() < stopAtTick))
            {
                performanceStartTick = simulation.GetTick();
                performanceStopwatch.Restart();
                simulation.StartSimulation();
                SendRunnerUpdateEvent(performanceStartTick, true);
            }
        }

        private void StopSimulationImpl()
        {
            if (simulation.IsRunning())
            {
                stopAtTick = 0;
                simulation.StopSimulation();
                performanceStopwatch.Stop();
                performanceStopTick = simulation.GetTick();
                SendRunnerUpdateEvent(performanceStopTick, false);
            }
        }
    }

}
