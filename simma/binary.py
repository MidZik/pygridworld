from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
from typing import Optional
from abc import ABC, abstractmethod
import shutil
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


@dataclass(frozen=True)
class PackedSimbin(BinaryProvider):
    """A structure of data on disk in a standardized format, containing an archive of code used
    to build the binary, plus all the binaries and metadata."""

    archive_file_name = 'code.tar.gz'
    meta_file_name = 'meta.json'

    path: Path
    name: str
    binary_name: str

    @staticmethod
    async def load_dir(path: Path):
        meta = await _utils.load_json(path / PackedSimbin.meta_file_name)
        name = meta['name']
        binary_name = meta['binary_name']
        src_archive = path / PackedSimbin.archive_file_name
        bin_dir = path / 'bin'
        binary_path = bin_dir / binary_name
        if not src_archive.is_file() or not binary_path.is_file() or not str(binary_path).startswith(str(bin_dir)):
            raise RuntimeError('PackedSimbin directory not formatted correctly.')
        return PackedSimbin(path.resolve(True), name, binary_name)

    @staticmethod
    async def create_from_local_simbin(path: Path, local_simbin: LocalSimbin):
        path.mkdir(exist_ok=False)
        src_archive = path / PackedSimbin.archive_file_name
        bin_dir = path / 'bin'
        bin_dir.mkdir()
        await local_simbin.copy_binary_files(bin_dir)
        await local_simbin.create_archive(src_archive)

        name = local_simbin.name
        binary_name = local_simbin.get_binary_path().name
        pack_timestamp = str(datetime.utcnow())
        meta = {
            'name': name,
            'binary_name': binary_name,
            'pack_timestamp': pack_timestamp
        }
        await _utils.dump_json(meta, path / PackedSimbin.meta_file_name)
        return PackedSimbin(path.resolve(True), name, binary_name)

    def get_binary_path(self) -> Path:
        return self.path / self.binary_name
