from distutils.cmd import Command
from distutils import log
from pathlib import Path
import subprocess
import setuptools
from distutils.command.build import build as _build
from setuptools.command.develop import develop as _develop
from shutil import which
import os


sln_files = [r"./SimulationServer/SimulationServer.sln"]


class BuildDotnetCommand(Command):
    description = "builds Visual Studio Solution files with dotnet"
    user_options = []

    def initialize_options(self) -> None:
        self.build_lib = None
        self.inplace = False

    def finalize_options(self) -> None:
        build = self.distribution.get_command_obj("build")
        build.ensure_finalized()
        self.build_lib = os.path.join(build.build_lib, r'simma\lib')

    def run(self) -> None:
        if which('dotnet') is None:
            raise RuntimeError("'dotnet' command is missing. Ensure that the .NET Core SDK is installed.")

        for file in sln_files:
            path = Path(file).resolve(True)

            self.announce(
                f"Building solution {path}...",
                level=log.INFO)

            if not self.inplace:
                cmd = [
                    'dotnet',
                    'publish',
                    str(path),
                    '-c', 'Release',
                    '-o', self.build_lib,
                    '-r', 'win-x64',
                    '--no-self-contained',
                    '-p:PublishLibAfterBuild=false'
                ]
            else:
                cmd = [
                    'dotnet',
                    'build',
                    str(path),
                    '-c', 'Release',
                    '-o', self.build_lib
                ]

            subprocess.check_call(cmd)


class Build(_build):
    sub_commands = _build.sub_commands + [('build_dotnet', None)]


class Develop(_develop):
    def install_for_development(self):
        self.reinitialize_command("build_dotnet", inplace=True)
        self.run_command("build_dotnet")

        return super().install_for_development()


setuptools.setup(
    cmdclass={
        'build_dotnet': BuildDotnetCommand,
        'build': Build,
        'develop': Develop
    },
    name='simma',
    version='0.1',
    description='Manage your simulations and results',
    author='Matt Idzik',
    author_email='matt.idzik1@gmail.com',
    packages=setuptools.find_packages(),
    include_package_data=True,
    setup_requires=['setuptools_git >= 0.3'],
    install_requires=[
        'PySide2>=5.13',
        'pyglet>=1.5.14',
        'grpcio>=1.33.2',
        'protobuf>=3.14'
    ],
    entry_points={
        'console_scripts': ['simma-app=simma.SimulationManagerApp:main']
    },
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'License :: Other/Proprietary License',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: C#',
        'Topic :: Scientific/Engineering'
    ]
)
