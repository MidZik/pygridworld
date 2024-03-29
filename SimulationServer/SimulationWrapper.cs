﻿using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Security.Cryptography.X509Certificates;

namespace SimulationServer
{
    class SimulationWrapper
    {
        public delegate void StringResultHandler(string s);
        public delegate void ULongResultHandler(ulong l);
        public delegate void BufferResultHandler(IntPtr buffer, ulong size);
        public delegate void SimEventHandler(string name, string data);
        public delegate void TickEventHandler(ulong tick, ulong flags);
        public delegate void CommandResultHandler([MarshalAs(UnmanagedType.LPUTF8Str)] string err, [MarshalAs(UnmanagedType.LPUTF8Str)] string output);

        delegate IntPtr CreateSimulationDelegate();
        CreateSimulationDelegate create_simulation;
        delegate void DestroySimulationDelegate(IntPtr sim);
        DestroySimulationDelegate destroy_simulation;
        delegate ulong GetTickDelegate(IntPtr sim);
        GetTickDelegate get_tick;
        delegate ulong GetStateJsonDelegate(IntPtr sim, IntPtr string_result_handler);
        GetStateJsonDelegate get_state_json;
        delegate void SetStateJsonDelegate(IntPtr sim, string json);
        SetStateJsonDelegate set_state_json;
        delegate ulong CreateEntityDelegate(IntPtr sim);
        CreateEntityDelegate create_entity;
        delegate void DestroyEntityDelegate(IntPtr sim, ulong eid);
        DestroyEntityDelegate destroy_entity;
        delegate ulong GetAllEntitiesDelegate(IntPtr sim, IntPtr ulong_result_handler);
        GetAllEntitiesDelegate get_all_entities;
        delegate void StartSimulationDelegate(IntPtr sim);
        StartSimulationDelegate start_simulation;
        delegate void StopSimulationDelegate(IntPtr sim);
        StopSimulationDelegate stop_simulation;
        delegate bool IsRunningDelegate(IntPtr sim);
        IsRunningDelegate is_running;
        delegate void AssignComponentDelegate(IntPtr sim, ulong eid, string component_name);
        AssignComponentDelegate assign_component;
        delegate ulong GetComponentJsonDelegate(IntPtr sim, IntPtr string_result_handler, ulong eid, string component_name);
        GetComponentJsonDelegate get_component_json;
        delegate void RemoveComponentDelegate(IntPtr sim, ulong eid, string component_name);
        RemoveComponentDelegate remove_component;
        delegate void ReplaceComponentDelegate(IntPtr sim, ulong eid, string component_name, string component_json);
        ReplaceComponentDelegate replace_component;
        delegate void GetComponentNamesDelegate(IntPtr sim, IntPtr string_result_handler);
        GetComponentNamesDelegate get_component_names;
        delegate ulong GetEntityComponentNamesDelegate(IntPtr sim, IntPtr string_result_handler, ulong eid);
        GetEntityComponentNamesDelegate get_entity_component_names;
        delegate ulong GetSingletonJsonDelegate(IntPtr sim, IntPtr string_result_handler, string singleton_name);
        GetSingletonJsonDelegate get_singleton_json;
        delegate void SetSingletonJsonDelegate(IntPtr sim, string singleton_name, string singleton_json);
        SetSingletonJsonDelegate set_singleton_json;
        delegate void GetSingletonNamesDelegate(IntPtr sim, IntPtr string_result_handler);
        GetSingletonNamesDelegate get_singleton_names;
        delegate void SetTickEventCallbackDelegate(IntPtr sim, IntPtr tick_event_result_handler);
        SetTickEventCallbackDelegate set_tick_event_callback;
        delegate ulong GetStateBinaryDelegate(IntPtr sim, IntPtr buffer_result_handler);
        GetStateBinaryDelegate get_state_binary;
        delegate void SetStateBinaryDelegate(IntPtr sim, IntPtr binary, ulong size);
        SetStateBinaryDelegate set_state_binary;
        delegate ulong GetEventsLastTickDelegate(IntPtr sim, IntPtr sim_event_handler);
        GetEventsLastTickDelegate get_events_last_tick;
        delegate void RunCommandDelegate(IntPtr sim, long argc, [In, MarshalAs(UnmanagedType.LPArray, ArraySubType = UnmanagedType.LPStr)] string[] argv, IntPtr command_result_handler);
        RunCommandDelegate run_command;
        delegate void RequestStopDelegate(IntPtr sim);
        RequestStopDelegate request_stop;

        IntPtr simulation_library_handle;
        IntPtr simulation_handle;
        TickEventHandler tick_event_handler = null;

        public SimulationWrapper(string simulation_library_path)
        {
            simulation_library_handle = NativeLibrary.Load(simulation_library_path);

            create_simulation = Marshal.GetDelegateForFunctionPointer<CreateSimulationDelegate>(GetExport("create_simulation"));
            destroy_simulation = Marshal.GetDelegateForFunctionPointer<DestroySimulationDelegate>(GetExport("destroy_simulation"));
            get_tick = Marshal.GetDelegateForFunctionPointer<GetTickDelegate>(GetExport("get_tick"));
            get_state_json = Marshal.GetDelegateForFunctionPointer<GetStateJsonDelegate>(GetExport("get_state_json"));
            set_state_json = Marshal.GetDelegateForFunctionPointer<SetStateJsonDelegate>(GetExport("set_state_json"));
            create_entity = Marshal.GetDelegateForFunctionPointer<CreateEntityDelegate>(GetExport("create_entity"));
            destroy_entity = Marshal.GetDelegateForFunctionPointer<DestroyEntityDelegate>(GetExport("destroy_entity"));
            get_all_entities = Marshal.GetDelegateForFunctionPointer<GetAllEntitiesDelegate>(GetExport("get_all_entities"));
            start_simulation = Marshal.GetDelegateForFunctionPointer<StartSimulationDelegate>(GetExport("start_simulation"));
            stop_simulation = Marshal.GetDelegateForFunctionPointer<StopSimulationDelegate>(GetExport("stop_simulation"));
            is_running = Marshal.GetDelegateForFunctionPointer<IsRunningDelegate>(GetExport("is_running"));
            assign_component = Marshal.GetDelegateForFunctionPointer<AssignComponentDelegate>(GetExport("assign_component"));
            get_component_json = Marshal.GetDelegateForFunctionPointer<GetComponentJsonDelegate>(GetExport("get_component_json"));
            remove_component = Marshal.GetDelegateForFunctionPointer<RemoveComponentDelegate>(GetExport("remove_component"));
            replace_component = Marshal.GetDelegateForFunctionPointer<ReplaceComponentDelegate>(GetExport("replace_component"));
            get_component_names = Marshal.GetDelegateForFunctionPointer<GetComponentNamesDelegate>(GetExport("get_component_names"));
            get_entity_component_names = Marshal.GetDelegateForFunctionPointer<GetEntityComponentNamesDelegate>(GetExport("get_entity_component_names"));
            get_singleton_json = Marshal.GetDelegateForFunctionPointer<GetSingletonJsonDelegate>(GetExport("get_singleton_json"));
            set_singleton_json = Marshal.GetDelegateForFunctionPointer<SetSingletonJsonDelegate>(GetExport("set_singleton_json"));
            get_singleton_names = Marshal.GetDelegateForFunctionPointer<GetSingletonNamesDelegate>(GetExport("get_singleton_names"));
            set_tick_event_callback = Marshal.GetDelegateForFunctionPointer<SetTickEventCallbackDelegate>(GetExport("set_tick_event_callback"));
            get_state_binary = Marshal.GetDelegateForFunctionPointer<GetStateBinaryDelegate>(GetExport("get_state_binary"));
            set_state_binary = Marshal.GetDelegateForFunctionPointer<SetStateBinaryDelegate>(GetExport("set_state_binary"));
            get_events_last_tick = Marshal.GetDelegateForFunctionPointer<GetEventsLastTickDelegate>(GetExport("get_events_last_tick"));
            run_command = Marshal.GetDelegateForFunctionPointer<RunCommandDelegate>(GetExport("run_command"));
            request_stop = Marshal.GetDelegateForFunctionPointer<RequestStopDelegate>(GetExport("request_stop"));

            simulation_handle = create_simulation();
        }

        ~SimulationWrapper()
        {
            destroy_simulation(simulation_handle);
            NativeLibrary.Free(simulation_library_handle);
        }

        private IntPtr GetExport(string name)
        {
            return NativeLibrary.GetExport(simulation_library_handle, name);
        }

        private IntPtr DelegateToUnmanaged<T>(T d) where T : Delegate
        {
            return Marshal.GetFunctionPointerForDelegate<T>(d);
        }

        public ulong GetTick()
        {
            return get_tick(simulation_handle);
        }

        public (string, ulong) GetStateJson()
        {
            string result = "";

            StringResultHandler handler = (string s) => { result = s; };

            ulong tick = get_state_json(simulation_handle, DelegateToUnmanaged(handler));

            GC.KeepAlive(handler);

            return (result, tick);
        }

        public void SetStateJson(string json)
        {
            set_state_json(simulation_handle, json);
        }

        public ulong CreateEntity()
        {
            return create_entity(simulation_handle);
        }

        public void DestroyEntity(ulong eid)
        {
            destroy_entity(simulation_handle, eid);
        }

        public (List<ulong>, ulong) GetAllEntities()
        {
            List<ulong> eids = new List<ulong>();

            ULongResultHandler handler = (ulong l) => { eids.Add(l); };

            ulong tick = get_all_entities(simulation_handle, DelegateToUnmanaged(handler));

            GC.KeepAlive(handler);

            return (eids, tick);
        }

        public void StartSimulation()
        {
            start_simulation(simulation_handle);
        }

        public void StopSimulation()
        {
            stop_simulation(simulation_handle);
        }

        public bool IsRunning()
        {
            return is_running(simulation_handle);
        }

        public void AssignComponent(ulong eid, string component_name)
        {
            assign_component(simulation_handle, eid, component_name);
        }

        public (string, ulong) GetComponentJson(ulong eid, string component_name)
        {
            string result = "";

            StringResultHandler handler = (string s) => { result = s; };

            ulong tick = get_component_json(simulation_handle, DelegateToUnmanaged(handler), eid, component_name);

            GC.KeepAlive(handler);

            return (result, tick);
        }

        public void RemoveComponent(ulong eid, string component_name)
        {
            remove_component(simulation_handle, eid, component_name);
        }

        public void ReplaceComponent(ulong eid, string component_name, string component_json)
        {
            replace_component(simulation_handle, eid, component_name, component_json);
        }

        public List<string> GetComponentNames()
        {
            List<string> names = new List<string>();

            StringResultHandler handler = (string s) => { names.Add(s); };

            get_component_names(simulation_handle, DelegateToUnmanaged(handler));

            GC.KeepAlive(handler);

            return names;
        }

        public (List<string>, ulong) GetEntityComponentNames(ulong eid)
        {
            List<string> names = new List<string>();

            StringResultHandler handler = (string s) => { names.Add(s); };

            ulong tick = get_entity_component_names(simulation_handle, DelegateToUnmanaged(handler), eid);

            GC.KeepAlive(handler);

            return (names, tick);
        }

        public (string, ulong) GetSingletonJson(string singleton_name)
        {
            string result = "";

            StringResultHandler handler = (string s) => { result = s; };

            ulong tick = get_singleton_json(simulation_handle, DelegateToUnmanaged(handler), singleton_name);

            GC.KeepAlive(handler);

            return (result, tick);
        }

        public void SetSingletonJson(string singleton_name, string singleton_json)
        {
            set_singleton_json(simulation_handle, singleton_name, singleton_json);
        }

        public List<string> GetSingletonNames()
        {
            List<string> names = new List<string>();

            StringResultHandler handler = (string s) => { names.Add(s); };

            get_singleton_names(simulation_handle, DelegateToUnmanaged(handler));

            GC.KeepAlive(handler);

            return names;
        }

        public void SetTickEventCallback(TickEventHandler callback)
        {
            tick_event_handler = callback;
            IntPtr handler_ptr = IntPtr.Zero;

            if (tick_event_handler != null)
            {
                handler_ptr = DelegateToUnmanaged<TickEventHandler>(tick_event_handler);
            }

            set_tick_event_callback(simulation_handle, handler_ptr);
        }

        public (byte[], ulong) GetStateBinary()
        {
            byte[] bin = null;

            BufferResultHandler handler = (IntPtr buf, ulong size) => { bin = new byte[size]; Marshal.Copy(buf, bin, 0, (int)size); };

            ulong tick = get_state_binary(simulation_handle, DelegateToUnmanaged(handler));

            GC.KeepAlive(handler);

            return (bin, tick);
        }

        public void SetStateBinary(byte[] bin)
        {
            var bin_handle = GCHandle.Alloc(bin, GCHandleType.Pinned);
            IntPtr ptr = bin_handle.AddrOfPinnedObject();
            set_state_binary(simulation_handle, ptr, (ulong)bin.Length);
            bin_handle.Free();
        }

        public ulong GetEventsLastTick(SimEventHandler callback)
        {
            ulong tick = get_events_last_tick(simulation_handle, DelegateToUnmanaged(callback));

            GC.KeepAlive(callback);

            return tick;
        }

        public (string, string) RunCommand(string[] args)
        {
            string err = null;
            string output = null;

            CommandResultHandler handler = (string _err, string _output) =>
            {
                err = _err;
                output = _output;
            };

            run_command(simulation_handle, args.Length, args, DelegateToUnmanaged(handler));

            GC.KeepAlive(handler);

            return (err, output);
        }

        public void RequestStop()
        {
            request_stop(simulation_handle);
        }
    }
}
