from distutils.cmd import Command
from distutils import log
from pathlib import Path
import subprocess
import setuptools
from distutils.command.build import build as _build
from shutil import which


sln_files = [r"./SimulationServer/SimulationServer.sln"]


def glob_fix(package_name, glob):
    # this assumes setup.py lives in the folder that contains the package
    package_path = Path(f'./{package_name}').resolve()
    return [str(path.relative_to(package_path))
            for path in package_path.glob(glob)]


class BuildDotnetCommand(Command):
    description = "builds Visual Studio Solution files with dotnet"
    user_options = []

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        if which('dotnet') is None:
            raise RuntimeError("'dotnet' command is missing. Ensure that the .NET Core SDK is installed.")

        for file in sln_files:
            path = Path(file).resolve(True)

            self.announce(
                f"Building solution {path}...",
                level=log.INFO)

            cmd = [
                'dotnet',
                'build',
                str(path),
                '-c', 'Release',
                '-o', 'simma/lib/',
            ]

            subprocess.check_call(cmd)


class Build(_build):
    sub_commands = _build.sub_commands + [('build_dotnet', None)]


setuptools.setup(
    cmdclass={
        'build_dotnet': BuildDotnetCommand,
        'build': Build
    },
    name='simma',
    version='0.1',
    description='Manage your simulations and results',
    author='Matt Idzik',
    author_email='matt.idzik1@gmail.com',
    packages=setuptools.find_packages(),
    package_data={
        'simma': [*glob_fix('simma', 'lib/**/*')]
    },
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
