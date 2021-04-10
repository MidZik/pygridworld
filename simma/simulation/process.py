"""
@author: Matt Idzik (MidZik)
"""

# TODO: based on simrunner, remove simrunner when this file is finalized

import asyncio
from subprocess import PIPE, DEVNULL
from typing import Optional

from simma.simulation.client import Client
from simma import LIB_PATH

_simulation_server_path = str(LIB_PATH / r'SimulationServer.exe')


async def simple_convert(input_file: str,
                         input_format: str,
                         input_sim_path: str,
                         output_file: str,
                         output_format: str,
                         output_sim_path: str = None):
    """Convert a single file

    :param input_file: File to convert
    :param input_format: The format of the input file ('json' or 'binary')
    :param input_sim_path: The path to the simulation binary of the input
    :param output_file: Where to put the output
    :param output_format: What format the output should be in ('json' or 'binary')
    :param output_sim_path: The path to the simulation binary for the output.
        If None, uses the input simulation binary.
    """
    args = [
        'convert',
        '-i', input_file,
        '-if', input_format,
        '-is', input_sim_path,
        '-o', output_file,
        '-of', output_format
    ]
    if output_sim_path:
        args.extend(('-os', output_sim_path))
    process = await asyncio.create_subprocess_exec(
        _simulation_server_path,
        *args,
        stdin=DEVNULL,
        stdout=DEVNULL
    )
    await process.communicate()
    if process.returncode != 0:
        raise RuntimeError("File conversion failed.")


async def convert_multiple(input_files,
                           input_format: str,
                           input_sim_path: str,
                           output_files,
                           output_format: str,
                           output_sim_path: str = None):
    """Convert multiple files in one go

    :param input_files: Iterable of files to convert
    :param input_format: The format of all the input files ('json' or 'binary')
    :param input_sim_path: The path to the simulation binary of the input
    :param output_files: Iterable of output paths, for each input file
    :param output_format: What format the outputs should be in ('json' or 'binary')
    :param output_sim_path: The path of the simulation binary for the output.
        In None, uses the input simulation binary.
    :return:
    """
    args = [
        'convert',
        '-if', input_format,
        '-is', input_sim_path,
        '-of', output_format,
        '-iofi'
    ]
    if output_sim_path:
        args.extend(('-os', output_sim_path))
    process = await asyncio.create_subprocess_exec(
        _simulation_server_path,
        *args,
        stdin=PIPE,
        stdout=DEVNULL
    )
    for i, o in zip(input_files, output_files):
        process.stdin.writelines((bytes(i, 'utf-8'), bytes(o, 'utf-8')))
        await process.stdin.drain()
    await process.communicate(b'\n')
    if process.returncode != 0:
        raise RuntimeError("File conversions failed.")


async def convert_multiple_generator(input_format: str,
                                     input_sim_path: str,
                                     output_format: str,
                                     output_sim_path: str = None):
    """Convert multiple files in one go. Input files must be passed into the generator.

    :param input_format: The format of all the input files ('json' or 'binary')
    :param input_sim_path: The path to the simulation binary of the input
    :param output_format: What format the outputs should be in ('json' or 'binary')
    :param output_sim_path: The path of the simulation binary for the output.
        In None, uses the input simulation binary.
    :return:
    """
    args = [
        'convert',
        '-if', input_format,
        '-is', input_sim_path,
        '-of', output_format,
        '-iofi'
    ]
    if output_sim_path:
        args.extend(('-os', output_sim_path))
    process = await asyncio.create_subprocess_exec(
        _simulation_server_path,
        *args,
        stdin=PIPE,
        stdout=PIPE
    )
    input_file = yield
    while input_file:
        process.stdin.writelines((bytes(input_file, 'utf-8'), b''))
        await process.stdin.drain()
        output = await process.stdout.readline()
        input_file = yield output
    await process.communicate(b'\n')
    if process.returncode != 0:
        raise RuntimeError("File conversions failed.")


async def create_default(output_file: str,
                         output_format: str,
                         output_sim_path: str):
    args = [
        'create-default',
        '-o', output_file,
        '-of', output_format,
        '-os', output_sim_path
    ]
    process = await asyncio.create_subprocess_exec(
        _simulation_server_path,
        *args,
        stdin=DEVNULL,
        stdout=DEVNULL
    )
    await process.communicate()
    if process.returncode != 0:
        raise RuntimeError("Creating default state file failed.")


class Process:
    def __init__(self, simulation_library_path):
        self._simulation_library_path = simulation_library_path

        self._process: Optional[asyncio.subprocess.Process] = None
        self._port = None
        self._channel = None
        self._lock = asyncio.Lock()

    async def start(self, owner_token=""):
        async with self._lock:
            if self._process is not None:
                return

            process = await asyncio.create_subprocess_exec(
                _simulation_server_path,
                'serve',
                '-o', owner_token,
                str(self._simulation_library_path),
                stdin=PIPE,
                stdout=PIPE
            )
            self._process = process

            process.stdin.write(b"port\n")
            await process.stdin.drain()
            line = await process.stdout.readline()
            self._port = int(line)

            self._channel = Client.make_channel(self.get_server_address())

    async def stop(self):
        async with self._lock:
            if self._process.returncode is not None:
                self._channel.close()
                self._channel = None
                self._port = None
                await self._process.communicate(b"exit\n")

    def get_port(self):
        if self._port:
            return self._port
        else:
            raise RuntimeError("Cannot get port: process not ready.")

    def get_server_address(self):
        return f'localhost:{self.get_port()}'

    def make_client(self, token=""):
        if self._channel is not None:
            return Client(self._channel, token)
        else:
            raise RuntimeError("Cannot make client: process not ready.")
