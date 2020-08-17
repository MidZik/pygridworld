using Grpc.Core;
using System;
using System.Linq;
using McMaster.Extensions.CommandLineUtils;

namespace SimulationServer
{
    
    class Program
    {
        static int Main(string[] args)
        {
            //System.Diagnostics.Debugger.Launch();

            var app = new CommandLineApplication
            {
                Name = "SimulationServer",
                Description = "Serves as an interface to simulation libraries."
            };

            app.HelpOption(inherited: true);

            app.OnExecute(() =>
            {
                Console.WriteLine("Subcommand must be specified.");
                app.ShowHelp();
                return 1;
            });

            app.Command("serve", serveCmd =>
            {
                serveCmd.Description = "Run a server that runs the specified simulation and provides a GRPC interface to it";
                var port = serveCmd.Option<int>("-p|--port <PORT>", "Port to run server on (automatically selected if not provided)", CommandOptionType.SingleValue)
                    .Accepts(v => v.Range(0, 65535));
                var simulation_library_path = serveCmd.Argument<string>("simulation", "The simulation library to serve")
                    .IsRequired()
                    .Accepts(v => v.ExistingFile());

                serveCmd.OnExecute(() =>
                {
                    SimulationWrapper wrapper = new SimulationWrapper(simulation_library_path.Value);

                    int server_port = 0;

                    if (port.HasValue())
                    {
                        server_port = port.ParsedValue;
                    }

                    Server server = new Server
                    {
                        Services = { Simulation.BindService(new SimulationService(wrapper)) },
                        Ports = { new ServerPort("localhost", server_port, ServerCredentials.Insecure) }
                    };

                    server.Start();

                    while (true)
                    {
                        string input = Console.ReadLine();

                        switch (input)
                        {
                            case "exit":
                                server.ShutdownAsync();
                                server.ShutdownTask.Wait();
                                return 0;
                            case "port":
                                Console.WriteLine(server.Ports.First().BoundPort);
                                break;
                            default:
                                Console.WriteLine("");
                                break;
                        }

                        Console.Out.Flush();
                    }
                });
            });

            try
            {
                return app.Execute(args);
            }
            catch (CommandParsingException ex)
            {
                Console.WriteLine(ex.Message);
                return 1;
            }
        }
    }
}
