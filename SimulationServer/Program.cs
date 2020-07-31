using Grpc.Core;
using System;
using System.Diagnostics;
using System.Linq;

namespace SimulationServer
{
    
    class Program
    {
        static void Main(string[] args)
        {
            //System.Diagnostics.Debugger.Launch();

            int server_port = 0;

            if (args.Length < 1)
            {
                Console.WriteLine("Missing simulation library path.");
                return;
            }

            if (args.Length >= 2)
            {
                server_port = int.Parse(args[1]);
            }

            string simulation_library_path = args[0];

            SimulationWrapper wrapper = new SimulationWrapper(simulation_library_path);

            Server server = new Server
            {
                Services = { Simulation.BindService(new SimulationService(wrapper)) },
                Ports = { new ServerPort("localhost", server_port, ServerCredentials.Insecure) }
            };

            server.Start();

            while(true)
            {
                string input = Console.ReadLine();

                switch(input)
                {
                    case "exit":
                        server.ShutdownAsync();
                        server.ShutdownTask.Wait();
                        return;
                    case "port":
                        Console.WriteLine(server.Ports.First().BoundPort);
                        break;
                    default:
                        Console.WriteLine("");
                        break;
                }

                Console.Out.Flush();
            }
        }
    }
}
