from dataclasses import dataclass
from pathlib import Path
import json
from typing import Optional
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod
from uuid import UUID, uuid4
import shutil
from datetime import datetime
import asyncio
import subprocess
from weakref import WeakValueDictionary

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

    async def create_archive(self, destination: Path):
        if destination.exists():
            raise FileExistsError(f'Cannot create archive at destination {destination}: already exists.')
        if self.archive_method == 'git-archive-working':
            git = await asyncio.create_subprocess_exec('git', 'ls-files', '-o', '-c', '--exclude-standard',
                                                       cwd=self.path.parent,
                                                       stdout=subprocess.PIPE)
            tar = await asyncio.create_subprocess_exec('tar', 'T', '-', '-czf', str(destination),
                                                       cwd=self.path.parent,
                                                       stdin=git.stdout)
            if await git.wait():
                raise RuntimeError("git encountered an error.")
            if await tar.wait():
                raise RuntimeError("tar encountered an error.")
        else:
            raise ValueError(f"Source file has unknown archive method: {self.archive_method}")

    async def copy_binary_files(self, destination_dir: Path):
        if not destination_dir.is_dir():
            raise NotADirectoryError(f'Cannot copy binary files to {destination_dir}: not a directory.')
        await asyncio.to_thread(shutil.copy2, self.get_binary_path(), destination_dir)
