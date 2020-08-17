using Grpc.Core;
using System;
using System.Linq;
using McMaster.Extensions.CommandLineUtils;
using System.IO;
using System.Text;
using System.Diagnostics;
using McMaster.Extensions.CommandLineUtils.Validation;
using System.ComponentModel.DataAnnotations;
using System.Runtime.InteropServices;

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

            app.Command("convert-bin", convertBinCmd =>
            {
                convertBinCmd.Description = "Convert a binary state file to a different format";

                var format = convertBinCmd.Option("-f|--format <FORMAT>", "The format to convert into", CommandOptionType.SingleValue)
                    .IsRequired()
                    .Accepts(v => v.Values("json"));

                var out_file = convertBinCmd.Option("-o|--output <FILES>", "If specified, the files to write the result into", CommandOptionType.MultipleValue)
                    .Accepts(v => v.LegalFilePath());

                var binary_file = convertBinCmd.Option("-b|--binary <FILES>", "The binary state files to convert. It must have been created by the provided simulation.", CommandOptionType.MultipleValue)
                    .IsRequired()
                    .Accepts(v => v.ExistingFile());

                var simulation_library_path = convertBinCmd.Argument("simulation", "The simulation library to use for conversion")
                    .IsRequired()
                    .Accepts(v => v.ExistingFile());

                convertBinCmd.OnValidate((context) =>
                {
                    if (out_file.HasValue())
                    {
                        if (out_file.Values.Count != binary_file.Values.Count)
                        {
                            return new ValidationResult("Number of output files does not match number of input files.");
                        }
                    }

                    return ValidationResult.Success;
                });

                convertBinCmd.OnExecute(() =>
                {
                    SimulationWrapper wrapper = new SimulationWrapper(simulation_library_path.Value);

                    for (int i = 0; i < binary_file.Values.Count; ++i)
                    {
                        byte[] bin = File.ReadAllBytes(binary_file.Values[i]);

                        wrapper.SetStateBinary(bin);

                        Stream out_stream;

                        if (out_file.HasValue())
                        {
                            out_stream = new FileStream(out_file.Values[i], FileMode.Create, FileAccess.Write);
                        }
                        else
                        {
                            out_stream = Console.OpenStandardOutput();
                        }

                        switch (format.Value())
                        {
                            case "json":
                                out_stream.Write(Encoding.UTF8.GetBytes(wrapper.GetStateJson()));
                                break;
                            default:
                                return 1;
                        }
                    }

                    return 0;
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
