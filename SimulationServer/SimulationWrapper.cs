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

        delegate IntPtr CreateSimulationDelegate();
        CreateSimulationDelegate create_simulation;
        delegate void DestroySimulationDelegate(IntPtr sim);
        DestroySimulationDelegate destroy_simulation;
        delegate ulong GetTickDelegate(IntPtr sim);
        GetTickDelegate get_tick;
        delegate void GetStateJsonDelegate(IntPtr sim, IntPtr string_result_handler);
        GetStateJsonDelegate get_state_json;
        delegate void SetStateJsonDelegate(IntPtr sim, string json);
        SetStateJsonDelegate set_state_json;
        delegate ulong CreateEntityDelegate(IntPtr sim);
        CreateEntityDelegate create_entity;
        delegate void DestroyEntityDelegate(IntPtr sim, ulong eid);
        DestroyEntityDelegate destroy_entity;
        delegate void GetAllEntitiesDelegate(IntPtr sim, IntPtr ulong_result_handler);
        GetAllEntitiesDelegate get_all_entities;
        delegate void StartSimulationDelegate(IntPtr sim);
        StartSimulationDelegate start_simulation;
        delegate void StopSimulationDelegate(IntPtr sim);
        StopSimulationDelegate stop_simulation;
        delegate bool IsRunningDelegate(IntPtr sim);
        IsRunningDelegate is_running;
        delegate void AssignComponentDelegate(IntPtr sim, ulong eid, string component_name);
        AssignComponentDelegate assign_component;
        delegate void GetComponentJsonDelegate(IntPtr sim, IntPtr string_result_handler, ulong eid, string component_name);
        GetComponentJsonDelegate get_component_json;
        delegate void RemoveComponentDelegate(IntPtr sim, ulong eid, string component_name);
        RemoveComponentDelegate remove_component;
        delegate void ReplaceComponentDelegate(IntPtr sim, ulong eid, string component_name, string component_json);
        ReplaceComponentDelegate replace_component;
        delegate void GetComponentNamesDelegate(IntPtr sim, IntPtr string_result_handler);
        GetComponentNamesDelegate get_component_names;
        delegate void GetEntityComponentNamesDelegate(IntPtr sim, IntPtr string_result_handler, ulong eid);
        GetEntityComponentNamesDelegate get_entity_component_names;
        delegate void GetSingletonJsonDelegate(IntPtr sim, IntPtr string_result_handler, string singleton_name);
        GetSingletonJsonDelegate get_singleton_json;
        delegate void SetSingletonJsonDelegate(IntPtr sim, string singleton_name, string singleton_json);
        SetSingletonJsonDelegate set_singleton_json;
        delegate void GetSingletonNamesDelegate(IntPtr sim, IntPtr string_result_handler);
        GetSingletonNamesDelegate get_singleton_names;
        delegate void SetEventCallbackDelegate(IntPtr sim, IntPtr string_result_handler);
        SetEventCallbackDelegate set_event_callback;

        IntPtr simulation_library_handle;
        IntPtr simulation_handle;

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
            set_event_callback = Marshal.GetDelegateForFunctionPointer<SetEventCallbackDelegate>(GetExport("set_event_callback"));

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

        public string GetStateJson()
        {
            string result = "";

            IntPtr handler = DelegateToUnmanaged<StringResultHandler>((string s) => { result = s; });

            get_state_json(simulation_handle, handler);

            return result;
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

        public List<ulong> GetAllEntities()
        {
            List<ulong> eids = new List<ulong>();

            IntPtr handler = DelegateToUnmanaged<ULongResultHandler>((ulong l) => { eids.Add(l); });

            get_all_entities(simulation_handle, handler);

            return eids;
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

        public string GetComponentJson(ulong eid, string component_name)
        {
            string result = "";

            IntPtr handler = DelegateToUnmanaged<StringResultHandler>((string s) => { result = s; });

            get_component_json(simulation_handle, handler, eid, component_name);

            return result;
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

            IntPtr handler = DelegateToUnmanaged<StringResultHandler>((string s) => { names.Add(s); });

            get_component_names(simulation_handle, handler);

            return names;
        }

        public List<string> GetEntityComponentNames(ulong eid)
        {
            List<string> names = new List<string>();

            IntPtr handler = DelegateToUnmanaged<StringResultHandler>((string s) => { names.Add(s); });

            get_entity_component_names(simulation_handle, handler, eid);

            return names;
        }

        public string GetSingletonJson(string singleton_name)
        {
            string result = "";

            IntPtr handler = DelegateToUnmanaged<StringResultHandler>((string s) => { result = s; });

            get_singleton_json(simulation_handle, handler, singleton_name);

            return result;
        }

        public void SetSingletonJson(string singleton_name, string singleton_json)
        {
            set_singleton_json(simulation_handle, singleton_name, singleton_json);
        }

        public List<string> GetSingletonNames()
        {
            List<string> names = new List<string>();

            IntPtr handler = DelegateToUnmanaged<StringResultHandler>((string s) => { names.Add(s); });

            get_singleton_names(simulation_handle, handler);

            return names;
        }

        public void SetEventCallback(StringResultHandler callback)
        {
            IntPtr handler = DelegateToUnmanaged<StringResultHandler>(callback);

            set_event_callback(simulation_handle, handler);
        }
    }
}
