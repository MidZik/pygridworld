"""
@author: Matt Idzik (MidZik)
"""
from pathlib import Path
import json
import re
import shutil
from uuid import UUID
from typing import Optional, List


class TimelineConfig:
    @staticmethod
    def create_from_path(path):
        config = TimelineConfig()
        config.load_from(path)
        return config

    def __init__(self):
        self.simulation_uuid: Optional[UUID] = None

    def load_from(self, path):
        path = Path(path).resolve(True)
        with path.open('r') as f:
            data = json.load(f)
            try:
                self.simulation_uuid = UUID(data['simulation_uuid'])
            except (LookupError, TypeError):
                self.simulation_uuid = None

    def save_to(self, path):
        path = Path(path).resolve()
        with path.open('w') as f:
            simulation_uuid = str(self.simulation_uuid) if self.simulation_uuid else None
            data = {
                'simulation_uuid': simulation_uuid
            }
            json.dump(data, f)


class Timeline:
    """
    Represents a timeline stored on disk
    """
    @staticmethod
    def point_file_name(tick):
        return f'tick-{tick}.point'

    @staticmethod
    def parse_point_file_name(file_name):
        exp = re.compile(r'^tick-(?P<tick>\d+)\.point$')
        result = exp.match(file_name)
        if result:
            return int(result.group('tick'))
        else:
            return None

    @staticmethod
    def create_timeline(path: Path, derive_from: Optional['Timeline'], derive_from_tick: Optional[int]):
        """
        Create and return a new timeline at a given location.
        :param path: The folder that the timeline should be created in. (Must not exist)
        :param derive_from: The timeline this timeline should be derived from
        :param derive_from_tick: If derived from a timeline, the tick at which it should be derived from
        :return: The newly created timeline.
        """
        path.mkdir()

        if derive_from is not None:
            derive_from.config.save_to(path / 'timeline.json')
            derive_from_tick = derive_from_tick if derive_from_tick is not None else derive_from.tick_list[0]
            derive_from_point_path = derive_from.get_point_file_path(derive_from_tick)
            new_point_path = path / Timeline.point_file_name(derive_from_tick)
            shutil.copyfile(str(derive_from_point_path), new_point_path)
        else:
            config = TimelineConfig()
            config.save_to(path / 'timeline.json')
            new_point_path = path / Timeline.point_file_name(0)
            new_point_path.touch(exist_ok=False)

        return Timeline(path)

    def __init__(self, path: Path):
        """
        :param path: The folder the timeline data resides in.
        """
        self.path: Path = path.resolve(True)
        self.config: TimelineConfig = TimelineConfig.create_from_path(self.get_config_file_path())

        self.tick_list: List[int] = []

        for point_path in self.path.glob('*.point'):
            tick = Timeline.parse_point_file_name(point_path.name)
            if tick is not None:
                self.tick_list.append(tick)

        self.tick_list.sort()

    def get_point_file_path(self, tick):
        return self.path / Timeline.point_file_name(tick)

    def get_config_file_path(self):
        return self.path / 'timeline.json'

    def save_config(self):
        self.config.save_to(self.get_config_file_path())

    def head(self):
        return self.tick_list[0]

    def tail(self):
        return self.tick_list[-1]
