from dataclasses import dataclass
from pathlib import Path
import json
from typing import Optional
from abc import ABC, abstractmethod
from uuid import UUID
import shutil
from datetime import datetime
import asyncio
import subprocess

from . import _utils


class BinaryProvider(ABC):
    @abstractmethod
    def get_binary_path(self) -> Path:
        pass


@dataclass(frozen=True)
class LocalSimbin(BinaryProvider):
    """A simbin file on the local machine, that describes where to find a simulation binary,
     and how to archive the code used to create it."""

    path: Path
    name: str
    binary_path: str
    archive_method: str
    archive_options: Optional[dict]

    @staticmethod
    async def load(path: Path):
        try:
            data = await _utils.load_json(path)

            name = data['name']
            binary_path = data['binary_path']
            archive_method = data['archive_method']
            archive_options = data.get('archive_options')
        except (LookupError, json.JSONDecodeError):
            raise ValueError('Simbin file not formatted correctly.')

        return LocalSimbin(path, name, binary_path, archive_method, archive_options)

    def get_binary_path(self) -> Path:
        return self.path.parent / self.binary_path


@dataclass(frozen=True)
class ProjectBinary(BinaryProvider):
    """A simulation binary that is saved in the project."""
    path: Path
    uuid: UUID
    simbin_name: str
    binary: str
    creation_timestamp: str

    @staticmethod
    async def create_from_local_simbin(path: Path, uuid: UUID, local_simbin: LocalSimbin):
        path.mkdir(exist_ok=False)
        try:
            binary_path = local_simbin.get_binary_path()

            src_dir = ProjectBinary._get_src_dir(path)
            src_dir.mkdir()
            bin_dir = ProjectBinary._get_bin_dir(path)
            bin_dir.mkdir()

            await asyncio.to_thread(shutil.copy2, binary_path, bin_dir)

            if local_simbin.archive_method == 'git-archive-working':
                archive_path = src_dir / 'code.tar.gz'
                git = subprocess.Popen(('git', 'ls-files', '-o', '-c', '--exclude-standard'),
                                       cwd=local_simbin.path.parent,
                                       stdout=subprocess.PIPE)
                subprocess.run(('tar', 'T', '-', '-czf', str(archive_path)),
                               cwd=local_simbin.path.parent,
                               stdin=git.stdout,
                               check=True)
                if git.wait():
                    raise RuntimeError("git encountered an error.")
            else:
                raise ValueError(f"Source file has unknown archive method: {local_simbin.archive_method}")

            data = {
                'uuid': str(uuid),
                'simbin_name': local_simbin.name,
                'binary': binary_path.name,
                'creation_timestamp': str(datetime.today())
            }

            await _utils.dump_json(data, ProjectBinary._get_config_path(path))

            project_binary = await ProjectBinary.load(path)

            await asyncio.to_thread(project_binary.set_description, "")

        except BaseException:
            shutil.rmtree(path)
            raise

        return project_binary

    @staticmethod
    async def load(path: Path):
        try:
            data = await _utils.load_json(ProjectBinary._get_config_path(path))

            uuid = UUID(data['uuid'])
            simbin_name = data['simbin_name']
            binary = data['binary']
            creation_timestamp = data['creation_timestamp']
        except (LookupError, json.JSONDecodeError):
            raise ValueError("Project binary config not formatted correctly.")

        return ProjectBinary(path, uuid, simbin_name, binary, creation_timestamp)

    @staticmethod
    def _get_config_path(path: Path):
        return path / 'binary.json'

    @staticmethod
    def _get_description_path(path: Path):
        return path / 'description.txt'

    @staticmethod
    def _get_src_dir(path: Path):
        return path / 'src'

    @staticmethod
    def _get_bin_dir(path: Path):
        return path / 'bin'

    def get_binary_path(self) -> Path:
        return self.path / self.binary

    def set_description(self, description):
        with ProjectBinary._get_description_path(self.path).open('w') as f:
            f.write(description)

    def get_description(self):
        with ProjectBinary._get_description_path(self.path).open() as f:
            return f.read()

    def get_description_summary(self):
        with ProjectBinary._get_description_path(self.path).open() as f:
            return f.readline(50).strip()

    async def delete(self):
        if ProjectBinary._get_config_path(self.path).exists():
            await asyncio.to_thread(shutil.rmtree, self.path)
