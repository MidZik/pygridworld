using Grpc.Core;
using System;
using System.Linq;
using McMaster.Extensions.CommandLineUtils;
using System.IO;
using System.Text;
using System.Diagnostics;
using System.ComponentModel.DataAnnotations;

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

            app.Command("convert", convertBinCmd =>
            {
                convertBinCmd.Description = "Convert a state file from one format and simulation version to another format and/or simulation version";

                var input_format = convertBinCmd.Option("-if|--input_format <FORMAT>", "The input file format", CommandOptionType.SingleValue)
                    .IsRequired()
                    .Accepts(v => v.Values("json", "binary"));

                var input = convertBinCmd.Option("-i|--input <FILE>", "The files to convert.", CommandOptionType.MultipleValue)
                    .Accepts(v => v.ExistingFile());

                var input_simulation = convertBinCmd.Option("-is|--input_sim <SIMULATION>", "The simulation the input file was generated from.", CommandOptionType.SingleValue)
                    .IsRequired()
                    .Accepts(v => v.ExistingFile());

                var output_format = convertBinCmd.Option("-of|--output_format <FORMAT>", "The output file format", CommandOptionType.SingleValue)
                    .IsRequired()
                    .Accepts(v => v.Values("json", "binary"));

                var output = convertBinCmd.Option("-o|--output <FILE>", "The files to write the results into.", CommandOptionType.MultipleValue)
                    .Accepts(v => v.LegalFilePath());

                var output_simulation = convertBinCmd.Option("-os|--output_sim <SIMULATION>", "The simulation to generate the output from. If not provided, will use input simulation.", CommandOptionType.SingleValue)
                    .Accepts(v => v.ExistingFile());

                var io_from_input = convertBinCmd.Option("-iofi|--io_from_input", "If specified, the input and output files will be read from the input stream in pairs of lines.", CommandOptionType.NoValue);

                convertBinCmd.OnValidate((context) =>
                {
                    if (io_from_input.HasValue() && (input.HasValue() || output.HasValue()))
                    {
                        return new ValidationResult("Cannot combine io_from_input flag with input or output options.");
                    }

                    if (!(io_from_input.HasValue() ^ input.HasValue()))
                    {
                        return new ValidationResult("Either --io_from_input or --input must be provided.");
                    }

                    if (output.HasValue())
                    {
                        if (output.Values.Count != input.Values.Count)
                        {
                            return new ValidationResult("Number of output files does not match number of input files.");
                        }
                    }

                    return ValidationResult.Success;
                });

                convertBinCmd.OnExecute(() =>
                {
                    string input_sim_path = Path.GetFullPath(input_simulation.Value());
                    SimulationWrapper input_wrapper = new SimulationWrapper(input_sim_path);
                    SimulationWrapper output_wrapper = input_wrapper;
                    if (output_simulation.HasValue())
                    {
                        string output_sim_path = Path.GetFullPath(output_simulation.Value());
                        if (output_sim_path != input_sim_path)
                        {
                            output_wrapper = new SimulationWrapper(output_sim_path);
                        }
                    }

                    if (io_from_input.HasValue())
                    {
                        while(true)
                        {
                            string read_input = Console.ReadLine();
                            if (string.IsNullOrWhiteSpace(read_input))
                            {
                                break;
                            }
                            string read_output = Console.ReadLine();
                            if (string.IsNullOrWhiteSpace(read_output))
                            {
                                break;
                            }
                            input.Values.Add(read_input);
                            output.Values.Add(read_output);
                        }
                    }

                    for (int i = 0; i < input.Values.Count; ++i)
                    {
                        switch (input_format.Value())
                        {
                            case "json":
                                input_wrapper.SetStateJson(File.ReadAllText(input.Values[i]));
                                break;
                            case "binary":
                                input_wrapper.SetStateBinary(File.ReadAllBytes(input.Values[i]));
                                break;
                            default:
                                return 1;
                        }

                        if (input_wrapper != output_wrapper)
                        {
                            // Converting versions, the json states are expected to work between versions
                            output_wrapper.SetStateJson(input_wrapper.GetStateJson());
                        }

                        Stream out_stream;

                        if (output.HasValue())
                        {
                            out_stream = new FileStream(output.Values[i], FileMode.Create, FileAccess.Write);
                        }
                        else
                        {
                            out_stream = Console.OpenStandardOutput();
                        }

                        switch (output_format.Value())
                        {
                            case "json":
                                out_stream.Write(Encoding.UTF8.GetBytes(output_wrapper.GetStateJson()));
                                break;
                            case "binary":
                                out_stream.Write(output_wrapper.GetStateBinary());
                                break;
                            default:
                                return 1;
                        }

                        out_stream.Flush();
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
