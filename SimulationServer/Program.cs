using Grpc.Core;
using System;
using System.Diagnostics;

namespace SimulationServer
{
    
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length < 1)
            {
                Console.WriteLine("Missing simulation library path.");
                return;
            }

            if (args.Length < 2)
            {
                Console.WriteLine("Missing port number.");
                return;
            }

            string simulation_library_path = args[0];
            int server_port = int.Parse(args[1]);

            SimulationWrapper wrapper = new SimulationWrapper(simulation_library_path);

            Server server = new Server
            {
                Services = { Simulation.BindService(new SimulationService(wrapper)) },
                Ports = { new ServerPort("localhost", server_port, ServerCredentials.Insecure) }
            };

            server.Start();

            Console.WriteLine($"Server started, hosting simulation \"{simulation_library_path}\" on port {server_port}.");

            server.ShutdownTask.Wait();
        }
    }
}
