using Grpc.Core;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Simma.Simulation;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Collections.Concurrent;
using System.Threading.Tasks.Dataflow;


namespace SimulationServer
{
    class PermissionDeniedException : Exception
    {
        public PermissionDeniedException() : base() { }

        public PermissionDeniedException(string message): base(message) { }
    }

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
        private string ownerToken = "";
        private string editorToken = "";

        private ReaderWriterLockSlim readerWriterLock = new ReaderWriterLockSlim();
        private AutoResetEvent noReadersEvent = new AutoResetEvent(false);
        private volatile int readerCount = 0;

        private Thread simulationThread;
        private bool simulationRunning = false;
        ulong currentTick = 0;

        public SimulationService(SimulationWrapper simulation, string ownerToken)
        {
            this.ownerToken = ownerToken ?? string.Empty;
            this.simulation = simulation;
        }

        private void RunSimulation()
        {
            List<EventMessage> event_messages = new List<EventMessage>();

            SimulationWrapper.SimEventHandler sim_event_handler = (string name, string json) =>
            {
                event_messages.Add(new EventMessage()
                {
                    Name = "sim." + name,
                    Json = json
                });
            };


            readerWriterLock.EnterWriteLock();
            try
            {
                while (simulationRunning)
                {
                    currentTick = simulation.Tick();
                    simulation.GetEventsLastTick(sim_event_handler);

                    if (currentTick % 500000 == 0)
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
                        events_committed?.Invoke(new EventsData { tick = currentTick, events = event_messages });
                        event_messages = new List<EventMessage>();
                    }

                    if (stopAtTick > 0 && currentTick >= stopAtTick)
                    {
                        simulationRunning = false;
                    }

                    if (readerCount > 0)
                    {
                        readerWriterLock.ExitWriteLock();
                        noReadersEvent.WaitOne();
                        readerWriterLock.EnterWriteLock();
                    }
                }
            }
            finally
            {
                readerWriterLock.ExitWriteLock();
            }
        }

        public override Task<AssignComponentResponse> AssignComponent(AssignComponentRequest request, ServerCallContext context)
        {
            AssertCalledByEditor(context);
            AssertNotRunning(context);

            readerWriterLock.EnterWriteLock();
            try
            {
                AssertNotRunning(context);
                simulation.AssignComponent(request.Eid, request.ComponentName);
            }
            finally
            {
                readerWriterLock.ExitWriteLock();
            }
            return Task.FromResult(new AssignComponentResponse { });
        }

        public override Task<CreateEntityResponse> CreateEntity(CreateEntityRequest request, ServerCallContext context)
        {
            AssertCalledByEditor(context);
            AssertNotRunning(context);

            ulong eid;

            readerWriterLock.EnterWriteLock();
            try
            {
                AssertNotRunning(context);
                eid = simulation.CreateEntity();
            }
            finally
            {
                readerWriterLock.ExitWriteLock();
            }
            return Task.FromResult(new CreateEntityResponse { Eid = eid });
        }

        public override Task<DestroyEntityResponse> DestroyEntity(DestroyEntityRequest request, ServerCallContext context)
        {
            AssertCalledByEditor(context);
            AssertNotRunning(context);

            readerWriterLock.EnterWriteLock();
            try
            {
                AssertNotRunning(context);
                simulation.DestroyEntity(request.Eid);
            }
            finally
            {
                readerWriterLock.ExitWriteLock();
            }
            
            return Task.FromResult(new DestroyEntityResponse { });
        }

        public override Task<GetAllEntitiesResponse> GetAllEntities(GetAllEntitiesRequest request, ServerCallContext context)
        {
            ulong tick;
            List<ulong> eids;

            StartReading();
            try
            {
                eids = simulation.GetAllEntities();
                tick = currentTick;
            }
            finally
            {
                StopReading();
            }

            GetAllEntitiesResponse result = new GetAllEntitiesResponse { Tick = tick };
            result.Eids.Add(eids);
            return Task.FromResult(result);
        }

        public override Task<GetComponentJsonResponse> GetComponentJson(GetComponentJsonRequest request, ServerCallContext context)
        {
            ulong tick;
            string json;

            StartReading();
            try
            {
                json = simulation.GetComponentJson(request.Eid, request.ComponentName);
                tick = currentTick;
            }
            finally
            {
                StopReading();
            }

            return Task.FromResult(new GetComponentJsonResponse { Json = json, Tick = tick });
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
            ulong tick;
            List<string> names;

            StartReading();
            try
            {
                names = simulation.GetEntityComponentNames(request.Eid);
                tick = currentTick;
            }
            finally
            {
                StopReading();
            }

            GetEntityComponentNamesResponse result = new GetEntityComponentNamesResponse { Tick = tick };
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
            ulong tick;
            string json;

            StartReading();
            try
            {
                json = simulation.GetSingletonJson(request.SingletonName);
                tick = currentTick;
            }
            finally
            {
                StopReading();
            }

            return Task.FromResult(new GetSingletonJsonResponse { Json = json, Tick = tick });
        }

        public override Task<GetSingletonNamesResponse> GetSingletonNames(GetSingletonNamesRequest request, ServerCallContext context)
        {
            List<string> names;

            StartReading();
            try
            {
                names = simulation.GetSingletonNames();
            }
            finally
            {
                StopReading();
            }

            GetSingletonNamesResponse result = new GetSingletonNamesResponse();
            result.SingletonNames.Add(names);
            return Task.FromResult(result);
        }

        public override Task<GetStateJsonResponse> GetStateJson(GetStateJsonRequest request, ServerCallContext context)
        {
            ulong tick;
            string json;

            StartReading();
            try
            {
                json = simulation.GetStateJson();
                tick = currentTick;
            }
            finally
            {
                StopReading();
            }

            return Task.FromResult(new GetStateJsonResponse { Json = json, Tick = tick });
        }

        public override Task<GetTickResponse> GetTick(GetTickRequest request, ServerCallContext context)
        {
            return Task.FromResult(new GetTickResponse { Tick = currentTick });
        }

        public override Task<IsRunningResponse> IsRunning(IsRunningRequest request, ServerCallContext context)
        {
            return Task.FromResult(new IsRunningResponse { Running = simulationRunning });
        }

        public override Task<RemoveComponentResponse> RemoveComponent(RemoveComponentRequest request, ServerCallContext context)
        {
            AssertCalledByEditor(context);
            AssertNotRunning(context);

            readerWriterLock.EnterWriteLock();
            try
            {
                AssertNotRunning(context);
                simulation.RemoveComponent(request.Eid, request.ComponentName);
            }
            finally
            {
                readerWriterLock.ExitWriteLock();
            }
            
            return Task.FromResult(new RemoveComponentResponse { });
        }

        public override Task<ReplaceComponentResponse> ReplaceComponent(ReplaceComponentRequest request, ServerCallContext context)
        {
            AssertCalledByEditor(context);
            AssertNotRunning(context);

            readerWriterLock.EnterWriteLock();
            try
            {
                AssertNotRunning(context);
                simulation.ReplaceComponent(request.Eid, request.ComponentName, request.Json);
            }
            finally
            {
                readerWriterLock.ExitWriteLock();
            }

            return Task.FromResult(new ReplaceComponentResponse { });
        }

        public override Task<SetSingletonJsonResponse> SetSingletonJson(SetSingletonJsonRequest request, ServerCallContext context)
        {
            AssertCalledByEditor(context);
            AssertNotRunning(context);

            readerWriterLock.EnterWriteLock();
            try
            {
                AssertNotRunning(context);
                simulation.SetSingletonJson(request.SingletonName, request.Json);
            }
            finally
            {
                readerWriterLock.ExitWriteLock();
            }
            
            return Task.FromResult(new SetSingletonJsonResponse { });
        }

        public override Task<SetStateJsonResponse> SetStateJson(SetStateJsonRequest request, ServerCallContext context)
        {
            AssertCalledByEditor(context);
            AssertNotRunning(context);

            readerWriterLock.EnterWriteLock();
            try
            {
                AssertNotRunning(context);
                simulation.SetStateJson(request.Json);
            }
            finally
            {
                readerWriterLock.ExitWriteLock();
            }
            
            return Task.FromResult(new SetStateJsonResponse { });
        }

        public override Task<StartSimulationResponse> StartSimulation(StartSimulationRequest request, ServerCallContext context)
        {
            AssertNotEditing(context);

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
            ulong tick;
            byte[] bin;

            StartReading();
            try
            {
                bin = simulation.GetStateBinary();
                tick = currentTick;
            }
            finally
            {
                StopReading();
            }

            return Task.FromResult(new GetStateBinaryResponse { Binary = Google.Protobuf.ByteString.CopyFrom(bin), Tick = tick });
        }

        public override Task<SetStateBinaryResponse> SetStateBinary(SetStateBinaryRequest request, ServerCallContext context)
        {
            AssertCalledByEditor(context);
            AssertNotRunning(context);

            readerWriterLock.EnterWriteLock();
            try
            {
                AssertNotRunning(context);
                simulation.SetStateBinary(request.Binary.ToByteArray());
            }
            finally
            {
                readerWriterLock.ExitWriteLock();
            }
            
            return Task.FromResult(new SetStateBinaryResponse { });
        }

        public override Task<RunCommandResponse> RunCommand(RunCommandRequest request, ServerCallContext context)
        {
            string err = null;
            string output = null;

            var args = request.Args;

            try
            {
                if (args.Count == 0)
                {
                    throw new ArgumentException("No command provided.");
                }
                else
                {
                    switch (args[0])
                    {
                        case "sim":
                            {
                                if (!IsEditor(context))
                                {
                                    err = $"'{args[0]}' command only allowed by editor.";
                                    break;
                                }

                                readerWriterLock.EnterWriteLock();
                                try
                                {
                                    (err, output) = simulation.RunCommand(args.Skip(1).ToArray());
                                }
                                finally
                                {
                                    readerWriterLock.ExitWriteLock();
                                }
                                break;
                            }
                        case "run":
                            {
                                if (IsEditingImpl())
                                {
                                    err = $"'{args[0]}' command only allowed while not in edit mode.";
                                    break;
                                }

                                StartSimulationImpl();
                                break;
                            }
                        case "run_until":
                            {
                                if (IsEditingImpl())
                                {
                                    err = $"'{args[0]}' command only allowed while not in edit mode.";
                                    break;
                                }

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
                                if (IsEditingImpl())
                                {
                                    err = $"'{args[0]}' command only allowed while not in edit mode.";
                                    break;
                                }

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
                                if (simulationRunning)
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
                                throw new ArgumentException($"Unknown command '{args[0]}'");
                            }
                    }
                }
            }
            catch (ArgumentException e)
            {
                err = e.Message;
                output = null;
            }
            catch (Exception)
            {
                err = "An unexpected error occured during the execution of the command.";
                output = null;
            }

            return Task.FromResult(new RunCommandResponse { Err = err ?? string.Empty, Output = output ?? string.Empty });

        }
        public override Task<SetEditorTokenResponse> SetEditorToken(SetEditorTokenRequest request, ServerCallContext context)
        {
            AssertCalledByOwner(context);
            AssertNotRunning(context);

            editorToken = request.Token;

            return Task.FromResult(new SetEditorTokenResponse());
        }

        public override Task<IsEditingResponse> IsEditing(IsEditingRequest request, ServerCallContext context)
        {
            bool result = false;
            if (request.CheckSelfOnly)
            {
                result = IsEditor(context);
            }
            else
            {
                result = IsEditingImpl();
            }
            return Task.FromResult(new IsEditingResponse { IsEditing = result });
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

            events_committed?.Invoke(new EventsData { tick = tick, events = event_messages });
        }

        private void StartSimulationImpl(ulong p_stopAtTick = 0)
        {
            lock (simulation)
            {
                stopAtTick = p_stopAtTick;
                if (!simulationRunning && (stopAtTick == 0 || currentTick < stopAtTick))
                {
                    performanceStartTick = currentTick;
                    simulationThread = new Thread(new ThreadStart(RunSimulation));
                    simulationRunning = true;
                    performanceStopwatch.Restart();
                    simulationThread.Start();
                    SendRunnerUpdateEvent(performanceStartTick, true);
                }
            }
        }

        private void StopSimulationImpl()
        {
            lock (simulation)
            {
                if (simulationRunning)
                {
                    simulationRunning = false;
                    simulationThread.Join();
                    performanceStopwatch.Stop();
                    performanceStopTick = currentTick;
                    SendRunnerUpdateEvent(performanceStopTick, false);
                }
            }
        }

        private bool IsEditingImpl()
        {
            return !string.IsNullOrEmpty(editorToken);
        }

        private string GetUserToken(ServerCallContext context)
        {
            return context.RequestHeaders.GetValue("x-user-token");
        }

        private bool IsEditor(ServerCallContext context)
        {
            return !string.IsNullOrEmpty(editorToken) && string.Equals(GetUserToken(context), editorToken);
        }

        private bool IsOwner(ServerCallContext context)
        {
            return !string.IsNullOrEmpty(ownerToken) && string.Equals(GetUserToken(context), ownerToken);
        }

        private void AssertCalledByEditor(ServerCallContext context)
        {
            if (!IsEditor(context))
            {
                string err = "Method can only be called by editor.";
                context.Status = new Status(StatusCode.PermissionDenied, err);
                throw new PermissionDeniedException(err);
            }
        }

        private void AssertCalledByOwner(ServerCallContext context)
        {
            if (string.IsNullOrEmpty(ownerToken))
            {
                string err = "Method can only be called by owner, and no owner is configured.";
                context.Status = new Status(StatusCode.FailedPrecondition, err);
                throw new InvalidOperationException(err);
            }

            if (!IsOwner(context))
            {
                string err = "Method can only be called by owner.";
                context.Status = new Status(StatusCode.PermissionDenied, err);
                throw new PermissionDeniedException(err);
            }
        }

        private void AssertNotEditing(ServerCallContext context)
        {
            if (IsEditingImpl())
            {
                string err = "Method can only be called while the simulation is not being edited.";
                context.Status = new Status(StatusCode.FailedPrecondition, err);
                throw new InvalidOperationException(err);
            }
        }

        private void AssertNotRunning(ServerCallContext context)
        {
            if (simulationRunning)
            {
                string err = "Method can only be called while the simulation is not running.";
                context.Status = new Status(StatusCode.FailedPrecondition, err);
                throw new InvalidOperationException(err);
            }
        }

        private void StartReading()
        {
            Interlocked.Increment(ref readerCount);
            readerWriterLock.EnterReadLock();
        }

        private void StopReading()
        {
            readerWriterLock.ExitReadLock();
            if (Interlocked.Decrement(ref readerCount) == 0)
            {
                noReadersEvent.Set();
            }
        }
    }
}
